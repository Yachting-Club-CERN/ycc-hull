"""
Helpers controller.
"""

from collections.abc import Sequence
from datetime import datetime, timedelta

from sqlalchemy import ColumnElement, and_, func, or_, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, defer, lazyload

from ycc_hull.config import emails_enabled
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.exceptions import (
    ControllerConflictException,
    ControllerNotFoundException,
)
from ycc_hull.controllers.notifications.helpers_notifications_controller import (
    HelpersNotificationsController,
)
from ycc_hull.db.entities import (
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
)
from ycc_hull.models.helpers_dtos import (
    HelperTaskCategoryDto,
    HelperTaskCreationRequestDto,
    HelperTaskDto,
    HelperTaskMarkAsDoneRequestDto,
    HelperTaskState,
    HelperTaskType,
    HelperTaskUpdateRequestDto,
    HelperTaskValidationRequestDto,
)
from ycc_hull.models.user import User
from ycc_hull.utils import get_now


class HelpersController(BaseController):
    """
    Helpers controller. Returns DTO objects.
    """

    def __init__(self) -> None:
        super().__init__()

        self._notifications = HelpersNotificationsController()

    async def find_all_task_categories(self) -> Sequence[HelperTaskCategoryDto]:
        return await self.database_context.query_all(
            select(HelperTaskCategoryEntity).order_by(HelperTaskCategoryEntity.title),
            async_transformer=HelperTaskCategoryDto.create,
        )

    async def find_all_tasks(
        self, *, year: int | None = None, published: bool | None = None
    ) -> Sequence[HelperTaskDto]:
        return await self._find_tasks(year=year, task_id=None, published=published)

    async def find_task_by_id(
        self,
        task_id: int,
        *,
        published: bool | None = None,
        session: Session | None = None,
    ) -> HelperTaskDto | None:
        return await self._find_task_by_id(
            task_id, published=published, session=session
        )

    async def get_task_by_id(
        self,
        task_id: int,
        *,
        published: bool | None = None,
        session: Session | None = None,
    ) -> HelperTaskDto:
        task = await self.find_task_by_id(task_id, published=published, session=session)
        if task:
            return task
        raise ControllerNotFoundException("Task not found")

    async def create_task(
        self, request: HelperTaskCreationRequestDto, user: User
    ) -> HelperTaskDto:
        # Admins/editors have full power (e.g., administer things happened in the past)
        with self.database_context.session() as session:
            try:
                task_entity = HelperTaskEntity(**request.model_dump())
                session.add(task_entity)
                session.commit()

                task = await HelperTaskDto.create(task_entity)
                self._logger.info("Created task: %s, user: %s", task, user)

                self._audit_log(session, user, "Helpers/Tasks/Create", {"new": task})

                return task
            except DatabaseError as exc:
                raise self._handle_database_error(  # pylint: disable=raising-bad-type
                    exc, what="create task", user=user, data=request
                )

    async def update_task(
        self,
        task_id: int,
        request: HelperTaskUpdateRequestDto,
        user: User,
    ) -> HelperTaskDto:
        # Admins/editors have full power (e.g., administer things happened in the past)
        with self.database_context.session() as session:
            old_task = await self._get_task_by_id(task_id, session=session)

            anyone_signed_up = old_task.captain or old_task.helpers
            same_timing = (
                request.starts_at == old_task.starts_at
                and request.ends_at == old_task.ends_at
                and request.deadline == old_task.deadline
            )

            # Check: cannot change timing if anyone has signed up
            if anyone_signed_up and not same_timing:
                raise ControllerConflictException(
                    "Cannot change timing after anyone has signed up"
                )
            # Check: must publish a task after anyone has signed up
            if anyone_signed_up and not request.published:
                raise ControllerConflictException(
                    "You must publish a task after anyone has signed up"
                )
            # Check: cannot change timing after the task has been marked as done
            if not same_timing and old_task.marked_as_done_at:
                raise ControllerConflictException(
                    "Cannot change timing after the task has been marked as done"
                )

            # Check: if a captain has signed up then the new licence must be active for the captain
            if old_task.captain and request.captain_required_licence_info_id != (
                old_task.captain_required_licence_info.id
                if old_task.captain_required_licence_info
                else None
            ):
                captain_entity = old_task.captain.member.get_entity()
                if not any(
                    licence_info_entity.infoid
                    == request.captain_required_licence_info_id
                    for licence_info_entity in captain_entity.active_licence_infos
                ):
                    raise ControllerConflictException(
                        "Cannot change captain required licence info because the signed up captain does not have the newly specified licence"
                    )

            # Check: cannot decrease helpers maximum count below signed up helpers count
            if request.helper_max_count < len(old_task.helpers):
                raise ControllerConflictException(
                    "Cannot decrease helpers maximum count below signed up helpers count"
                )

            try:
                task_entity = old_task.get_entity()
                old_task = await HelperTaskDto.create(task_entity)
                self._update_entity_from_dto(task_entity, request)
                session.commit()

                new_task = await HelperTaskDto.create(task_entity)
                self._logger.info("Updated task: %s, user: %s", new_task, user)

                self._audit_log(
                    session,
                    user,
                    f"Helpers/Tasks/Update/{task_id}",
                    {"old": old_task, "new": new_task},
                )

                return new_task
            except DatabaseError as exc:
                raise self._handle_database_error(  # pylint: disable=raising-bad-type
                    exc, what="update task", user=user, data=request
                )

    async def sign_up_as_captain(self, task_id: int, user: User) -> None:
        with self.database_context.session() as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)

            self._check_can_sign_up(task=task, member_id=user.member_id)
            if task.captain:
                raise ControllerConflictException("Task already has a captain")

            if task.captain_required_licence_info:
                required_licence = task.captain_required_licence_info.licence
                if not user.has_licence(required_licence):
                    raise ControllerConflictException(
                        f"Task captain needs licence: {required_licence}"
                    )

            task_entity = await self._get_task_entity_by_id(task_id, session=session)
            task_entity.captain_id = user.member_id
            task_entity.captain_signed_up_at = get_now()
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._audit_log(session, user, f"Helpers/Tasks/SignUpAsCaptain/{task_id}")
            self._run_in_background(self._notifications.on_sign_up(updated_task, user))

    async def sign_up_as_helper(self, task_id: int, user: User) -> None:
        with self.database_context.session() as session:
            task = await self.get_task_by_id(task_id, published=True, session=session)

            self._check_can_sign_up(task=task, member_id=user.member_id)
            if len(task.helpers) >= task.helper_max_count:
                raise ControllerConflictException("Task helper limit reached")

            helper = HelperTaskHelperEntity(
                task_id=task.id, member_id=user.member_id, signed_up_at=get_now()
            )
            session.add(helper)

            session.commit()

            updated_task = await self.get_task_by_id(
                task_id, published=True, session=session
            )
            self._audit_log(session, user, f"Helpers/Tasks/SignUpAsHelper/{task_id}")
            self._run_in_background(self._notifications.on_sign_up(updated_task, user))

    async def mark_as_done(
        self, task_id: int, request: HelperTaskMarkAsDoneRequestDto, user: User
    ) -> None:
        with self.database_context.session() as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)

            if task.state != HelperTaskState.PENDING:
                raise ControllerConflictException("Task already marked as done")
            if self._starts_in_the_future(task):
                raise ControllerConflictException(
                    "Cannot mark a task as done before it starts"
                )

            task_entity = await self._get_task_entity_by_id(task_id, session=session)
            task_entity.marked_as_done_at = get_now()
            task_entity.marked_as_done_by_id = user.member_id
            task_entity.marked_as_done_comment = request.comment
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._audit_log(session, user, f"Helpers/Tasks/MarkAsDone/{task_id}")
            self._run_in_background(
                self._notifications.on_mark_as_done(updated_task, user)
            )

    async def validate(
        self, task_id: int, request: HelperTaskValidationRequestDto, user: User
    ) -> None:
        with self.database_context.session() as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)

            if task.state == HelperTaskState.VALIDATED:
                raise ControllerConflictException("Task already validated")
            if self._starts_in_the_future(task):
                raise ControllerConflictException(
                    "Cannot validate a task before it starts"
                )

            helper_ids_in_db = set(helper.member.id for helper in task.helpers)
            helper_ids_in_request = set(
                helper.member.id
                for helper in request.helpers_to_validate + request.helpers_to_remove
            )

            if helper_ids_in_db != helper_ids_in_request:
                raise ControllerConflictException(
                    "Validation request is missing helpers"
                )

            to_be_removed = set(
                helper.member.id for helper in request.helpers_to_remove
            )

            task_entity = await self._get_task_entity_by_id(task_id, session=session)
            now = get_now()

            if not task_entity.marked_as_done_at:
                task_entity.marked_as_done_at = now
                task_entity.marked_as_done_by_id = user.member_id

            task_entity.validated_at = now
            task_entity.validated_by_id = user.member_id
            task_entity.validation_comment = request.comment

            for helper_entity in await task_entity.awaitable_attrs.helpers:
                if helper_entity.member_id in to_be_removed:
                    session.delete(helper_entity)

            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._audit_log(session, user, f"Helpers/Tasks/Validate/{task_id}")
            self._run_in_background(self._notifications.on_validate(updated_task, user))

    async def send_daily_reminders(self) -> None:  # pylint: disable=too-many-locals
        """
        Sends daily reminders to task participants.

        Never send reminders for:
        - Tasks that are started and are not yet finished (especially multi-day shifts)
        - Tasks that are validated

        For upcoming tasks send reminders:
        - 2 weeks before
        - 3 days before
        - the day of the task

        Overdue tasks (not validated tasks in the past; to speed up task validation):
        - Reminders are sent per contact, not per task
        - Shifts (and invalid timing):
            - A reminder is sent every day to the contact 1 week after the shift is finished.
            - The delay gives a window for shift organisers to validate tasks (as shifts "just happen" anyway").
            - No immediate pressure on shift organisers, especially as the shifts often happen in batches (regattas, surveillance etc.)
        - Deadline tasks:
            - A reminder is sent every day to the contact the if the deadline has expired.
            - Deadline tasks are usually one-off maintenance tasks and in the past the experience was that they are often forgotten
            - After the deadline expires, it is either done (and should have been validated) or the deadline should be extended

        Notes:
        - Also send reminders for past years (avoid hanging tasks; tasks can have a deadline on 31 December)
        - Also send reminders for unpublished tasks (tasks with helpers should not be unpublished)
        """
        if not emails_enabled(self._logger):
            return

        def debug(task: HelperTaskDto, message: str) -> None:
            self._logger.debug(
                "Task %s (id=%d, starts_at=%s, ends_at=%s, deadline=%s): %s",
                task.title,
                task.id,
                task.starts_at,
                task.ends_at,
                task.deadline,
                message,
            )

        with self.database_context.session() as session:
            # Query all relevant tasks
            now = get_now()

            # "Round" to the start of the day
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            one_week_ago = now - timedelta(days=7)

            # Using ranges to avoid persisting notification time in the database
            due_in_2_weeks_start = today_start + timedelta(days=14)
            due_in_2_weeks_end = today_end + timedelta(days=14)
            due_in_3_days_start = today_start + timedelta(days=3)
            due_in_3_days_end = today_end + timedelta(days=3)

            entity_timing_fields = [
                HelperTaskEntity.starts_at,
                HelperTaskEntity.ends_at,
                HelperTaskEntity.deadline,
            ]

            where = and_(
                HelperTaskEntity.validated_by_id.is_(None),
                or_(
                    # Note: BETWEEN is inclusive (uses <=, not <)
                    *[
                        field.between(due_in_2_weeks_start, due_in_2_weeks_end)
                        for field in entity_timing_fields
                    ],
                    *[
                        field.between(due_in_3_days_start, due_in_3_days_end)
                        for field in entity_timing_fields
                    ],
                    # Today or overdue
                    *[field <= today_end for field in entity_timing_fields],
                ),
            )

            tasks = await self._find_tasks(
                year=None,
                task_id=None,
                published=None,
                where=where,
                session=session,
            )

            # Split tasks how should be the reminders sent
            upcoming_tasks: list[HelperTaskDto] = []
            overdue_tasks: list[HelperTaskDto] = []

            for task in tasks:
                timings = [
                    t
                    for t in [task.starts_at, task.ends_at, task.deadline]
                    if t is not None
                ]

                if not timings:
                    # (Invalid) task has no timing information: no reminder
                    self._logger.warning("Task %s has no timing information", task)
                    continue

                timing_earliest = min(timings)
                timing_latest = max(timings)

                # Note that here we are actually comparing to now, not to the start of the day
                task_upcoming = now < timing_earliest
                task_due = timing_latest < now

                if not task_upcoming and not task_due:
                    # Ongoing tasks: no reminder
                    debug(task, "Ongoing task")
                    continue

                if (
                    task_due
                    and task.type == HelperTaskType.SHIFT
                    and one_week_ago < timing_latest
                ):
                    # Shifts: reminder 1 week after the shift ends
                    debug(task, "Overdue shift in grace period")
                    continue

                if task_due:
                    debug(task, "Overdue task")
                    overdue_tasks.append(task)
                else:
                    debug(task, "Upcoming task")
                    upcoming_tasks.append(task)

        self._logger.info(
            "Identified %d upcoming tasks and %d overdue tasks",
            len(upcoming_tasks),
            len(overdue_tasks),
        )
        await self._notifications.send_reminders(upcoming_tasks, overdue_tasks)

    async def _find_tasks(  # pylint: disable=too-many-arguments
        self,
        *,
        year: int | None,
        task_id: int | None,
        published: bool | None,
        where: ColumnElement[bool] | None = None,
        session: Session | None = None,
    ) -> Sequence[HelperTaskDto]:
        query = select(HelperTaskEntity)

        exclude_large_fields: bool = task_id is None

        if exclude_large_fields:
            query = query.options(
                defer(HelperTaskEntity.long_description, raiseload=True),
                defer(HelperTaskEntity.marked_as_done_comment, raiseload=True),
                defer(HelperTaskEntity.validation_comment, raiseload=True),
            )

        if year is not None:
            query = query.where(
                func.coalesce(  # pylint: disable=not-callable
                    HelperTaskEntity.starts_at, HelperTaskEntity.deadline
                ).between(
                    datetime(year, 1, 1, 0, 0, 0, 0),
                    datetime(year, 12, 31, 23, 59, 59, 0),
                )
            )
        if task_id is not None:
            query = query.where(HelperTaskEntity.id == task_id)
        if published is not None:
            query = query.where(HelperTaskEntity.published == published)
        if where is not None:
            query = query.where(where)

        query = query.order_by(
            HelperTaskEntity.urgent.desc(),
            func.coalesce(  # pylint: disable=not-callable
                HelperTaskEntity.starts_at, HelperTaskEntity.deadline
            ).asc(),
        )

        return await self.database_context.query_all(
            query,
            async_transformer=(
                HelperTaskDto.create_without_large_fields
                if exclude_large_fields
                else HelperTaskDto.create
            ),
            unique=True,
            session=session,
        )

    async def _find_task_by_id(
        self,
        task_id: int,
        *,
        published: bool | None,
        session: Session | None = None,
    ) -> HelperTaskDto | None:
        tasks = await self._find_tasks(
            year=None, task_id=task_id, published=published, session=session
        )
        return tasks[0] if tasks else None

    async def _get_task_by_id(
        self,
        task_id: int,
        *,
        published: bool | None = None,
        session: Session | None = None,
    ) -> HelperTaskDto:
        task = await self._find_task_by_id(
            task_id, published=published, session=session
        )
        if task:
            return task
        raise ControllerNotFoundException(
            "Task not found or not published" if published else "Task not found"
        )

    async def _get_task_entity_by_id(
        self, task_id: int, *, session: Session
    ) -> HelperTaskEntity:
        return (
            session.scalars(
                select(HelperTaskEntity)
                .options(lazyload("*"))
                .where(HelperTaskEntity.id == task_id)
            )
        ).one()

    def _check_can_sign_up(self, *, task: HelperTaskDto, member_id: int) -> None:
        if not task.published:
            raise ControllerConflictException("Cannot sign up to an unpublished task")
        if task.state == HelperTaskState.DONE:
            raise ControllerConflictException("Cannot sign up to a task marked as done")
        if task.state == HelperTaskState.VALIDATED:
            raise ControllerConflictException("Cannot sign up to a validated task")

        now = get_now()
        if (task.starts_at and task.starts_at < now) or (
            task.deadline and task.deadline < now
        ):
            raise ControllerConflictException("Cannot sign up to a task in the past")

        if task.captain and task.captain.member.id == member_id:
            raise ControllerConflictException("Already signed up as captain")
        if any(helper.member.id == member_id for helper in task.helpers):
            raise ControllerConflictException("Already signed up as helper")

    def _starts_in_the_future(self, task: HelperTaskDto) -> bool:
        return bool(task.starts_at and task.starts_at > get_now())
