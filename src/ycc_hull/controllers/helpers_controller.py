"""
Helpers controller.
"""

from collections.abc import Sequence
from datetime import date, datetime, timedelta

from sqlalchemy import ColumnElement, and_, func, or_, select
from sqlalchemy.orm import Session, defer

from ycc_hull.config import CONFIG
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.exceptions import (
    ControllerConflictException,
    ControllerNotFoundException,
)
from ycc_hull.controllers.notifications.helpers_notifications_controller import (
    HelpersNotificationsController,
)
from ycc_hull.db.entities import (
    HelpersAppPermissionEntity,
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
    LicenceEntity,
    MemberEntity,
)
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import (
    HelpersAppPermissionDto,
    HelpersAppPermissionGrantRequestDto,
    HelpersAppPermissionUpdateRequestDto,
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
from ycc_hull.utils import deep_diff, get_now


class HelpersController(BaseController):
    """
    Helpers controller. Returns DTO objects.
    """

    def __init__(self) -> None:
        super().__init__()

        self._notifications = HelpersNotificationsController()

    async def find_all_permissions(self) -> Sequence[HelpersAppPermissionDto]:
        return await self.database_context.query_all(
            select(HelpersAppPermissionEntity)
            .join(HelpersAppPermissionEntity.member)
            .order_by(MemberEntity.name, MemberEntity.firstname),
            async_transformer=HelpersAppPermissionDto.create,
        )

    async def grant_permission(
        self, request: HelpersAppPermissionGrantRequestDto, user: User
    ) -> HelpersAppPermissionDto:
        with self.database_action(
            action="Helpers / Grant Permission", user=user, details={"request": request}
        ) as session:
            permission_entity = HelpersAppPermissionEntity(**request.model_dump())
            session.add(permission_entity)
            session.commit()

            permission = await HelpersAppPermissionDto.create(permission_entity)
            self._logger.info(
                "Granted permission: %s, user: %s", permission, user.username
            )

            self._audit_log(
                session, user, "Helpers/Permissions/Grant", {"new": permission}
            )

            return permission

    async def update_permission(
        self, member_id: int, request: HelpersAppPermissionUpdateRequestDto, user: User
    ) -> HelpersAppPermissionDto:
        with self.database_action(
            action="Helpers / Update Permission",
            user=user,
            details={"member_id": member_id, "request": request},
        ) as session:
            original_permission = await self._get_permission_by_id(
                member_id, session=session
            )

            permission_entity = original_permission.get_entity()
            self._update_entity_from_dto(permission_entity, request)
            session.commit()

            updated_permission = await HelpersAppPermissionDto.create(permission_entity)
            self._logger.info(
                "Updated permission: %s, user: %s", updated_permission, user.username
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Permissions/Update/{member_id}",
                {
                    "diff": deep_diff(original_permission, updated_permission),
                    "old": original_permission,
                    "new": updated_permission,
                },
            )

            return updated_permission

    async def revoke_permission(self, member_id: int, user: User) -> None:
        if member_id == user.member_id:
            raise ControllerConflictException("You cannot revoke your own permissions")

        with self.database_action(
            action="Helpers / Revoke Permission",
            user=user,
            details={"member_id": member_id},
        ) as session:
            permission = await self._get_permission_by_id(member_id, session=session)

            permission_entity = permission.get_entity()
            session.delete(permission_entity)
            session.commit()

            self._logger.info(
                "Revoked permission: %s, user: %s",
                permission,
                user.username,
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Permissions/Revoke/{member_id}",
                {
                    "old": permission,
                },
            )

    async def _get_permission_by_id(
        self, member_id: int, *, session: Session
    ) -> HelpersAppPermissionDto:
        entries = await self.database_context.query_all(
            select(HelpersAppPermissionEntity).where(
                HelpersAppPermissionEntity.member_id == member_id
            ),
            async_transformer=HelpersAppPermissionDto.create,
            session=session,
        )

        if entries:
            return entries[0]

        raise ControllerNotFoundException("Permission not found")

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
        with self.database_action(
            action="Helper Task / Create", user=user, details={"request": request}
        ) as session:
            task_entity = HelperTaskEntity(**request.model_dump())
            session.add(task_entity)
            session.commit()

            task = await HelperTaskDto.create(task_entity)
            self._logger.info("Created task: %s, user: %s", task.id, user.username)

            self._audit_log(session, user, "Helpers/Tasks/Create", {"new": task})

            return task

    async def update_task(
        self,
        task_id: int,
        request: HelperTaskUpdateRequestDto,
        user: User,
    ) -> HelperTaskDto:
        with self.database_action(
            action="Helper Task / Update",
            user=user,
            details={"task_id": task_id, "request": request},
        ) as session:
            original_task = await self._get_task_by_id(task_id, session=session)

            await self._check_can_update_task(request, original_task)

            task_entity = original_task.get_entity()
            self._update_entity_from_dto(task_entity, request)
            if original_task.validated_by is not None:
                task_entity.urgent = False
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Updated task: %s, user: %s", updated_task.id, user.username
            )

            # Calculate change
            diff = deep_diff(original_task, updated_task)

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/Update/{task_id}",
                {
                    "diff": diff,
                    "old": original_task,
                    "new": updated_task,
                    "notifySignedUpMembers": request.notify_signed_up_members,
                },
            )
            if request.notify_signed_up_members:
                self._logger.info(
                    "Notifying signed up members about the task update (ID: %d), updated fields: %s",
                    task_id,
                    diff.keys(),
                )
                self._run_in_background(
                    self._notifications.on_update(
                        original_task, updated_task, diff, user
                    )
                )
            else:
                self._logger.info(
                    "NOT notifying signed up members about the task update (ID: %d), updated fields: %s",
                    task_id,
                    diff.keys(),
                )

            return updated_task

    async def _check_can_update_task(
        self, request: HelperTaskUpdateRequestDto, original_task: HelperTaskDto
    ) -> None:
        anyone_signed_up = original_task.captain or original_task.helpers

        # Check: Cannot change the task year if anyone has signed up
        # Active Members change over year, but let's rather save the complicated check, since this should not be a main use case
        if anyone_signed_up and original_task.year != request.year:
            raise ControllerConflictException(
                "You cannot change the year of the task after anyone has signed up. Please create a new task instead."
            )

        if anyone_signed_up and not request.published:
            raise ControllerConflictException(
                "You must publish a task after anyone has signed up"
            )

        # Check: If a captain has signed up then the new licence must be active for the captain
        if (
            original_task.captain
            and request.captain_required_licence_info_id is not None
            and request.captain_required_licence_info_id
            != (
                original_task.captain_required_licence_info.id
                if original_task.captain_required_licence_info
                else None
            )
        ):
            captain_entity = original_task.captain.member.get_entity()
            if not any(
                licence_info_entity.infoid == request.captain_required_licence_info_id
                for licence_info_entity in captain_entity.active_licence_infos
            ):
                raise ControllerConflictException(
                    "Cannot change captain required licence info because the signed up captain does not have the newly specified licence"
                )

        # Check: Cannot set the maximum number of helpers below the number of already signed-up helpers
        signed_up_helper_count = len(original_task.helpers)
        if request.helper_max_count < signed_up_helper_count:
            raise ControllerConflictException(
                f"Cannot set the maximum number of helpers below the number of already signed-up helpers ({signed_up_helper_count})"
            )

    async def set_captain(
        self, task_id: int, member_id: int, user: User
    ) -> HelperTaskDto:
        with self.database_action(
            action="Helper Task / Set Captain",
            user=user,
            details={"task_id": task_id, "member_id": member_id},
        ) as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)
            await self._check_can_sign_up_as_captain(
                task=task, member_id=member_id, editor_action=True, session=session
            )

            task_entity = task.get_entity()
            task_entity.captain_id = member_id
            task_entity.captain_signed_up_at = get_now()
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            if not updated_task.captain:
                raise RuntimeError(
                    f"Did set the captain to {member_id}, but it appears to be unset: {updated_task}"
                )

            self._logger.info(
                "Set captain for task: %s, captain: %s, user: %s",
                updated_task.id,
                updated_task.captain.member.username,
                user.username,
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/SetCaptain/{task_id}/Captain/{member_id}",
            )
            self._run_in_background(
                self._notifications.on_add_helper(
                    updated_task, updated_task.captain.member, user
                )
            )

            return updated_task

    async def remove_captain(self, task_id: int, user: User) -> HelperTaskDto:
        with self.database_action(
            action="Helper Task / Remove Captain",
            user=user,
            details={"task_id": task_id},
        ) as session:
            original_task = await self._get_task_by_id(
                task_id, published=True, session=session
            )

            if not original_task.captain:
                raise ControllerConflictException("Task has no captain")
            original_captain = original_task.captain.member

            task_entity = original_task.get_entity()
            task_entity.captain_id = None
            task_entity.captain_signed_up_at = None
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Removed captain from task: %s, original captain: %s, user: %s",
                updated_task.id,
                original_captain.username,
                user.username,
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/RemoveCaptain/{task_id}/Captain/{original_captain.id}",
            )
            self._run_in_background(
                self._notifications.on_remove_helper(
                    updated_task, original_captain, user
                )
            )

            return updated_task

    async def add_helper(
        self, task_id: int, member_id: int, user: User
    ) -> HelperTaskDto:
        with self.database_action(
            action="Helper Task / Add Helper",
            user=user,
            details={"task_id": task_id, "member_id": member_id},
        ) as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)
            await self._check_can_sign_up_as_helper(
                task=task, member_id=member_id, editor_action=True, session=session
            )

            helper_entity = HelperTaskHelperEntity(
                task_id=task.id, member_id=member_id, signed_up_at=get_now()
            )
            session.add(helper_entity)
            session.commit()

            updated_task = await self.get_task_by_id(
                task_id, published=True, session=session
            )
            helper = await MemberPublicInfoDto.create(
                await helper_entity.awaitable_attrs.member
            )

            self._logger.info(
                "Added helper to task: %s, helper: %s, user: %s",
                updated_task.id,
                helper.username,
                user.username,
            )
            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/AddHelper/{task_id}/Helper/{member_id}",
            )
            self._run_in_background(
                self._notifications.on_add_helper(updated_task, helper, user)
            )

            return updated_task

    async def remove_helper(
        self, task_id: int, member_id: int, user: User
    ) -> HelperTaskDto:
        with self.database_action(
            action="Helper Task / Remove Helper",
            user=user,
            details={"task_id": task_id, "member_id": member_id},
        ) as session:
            original_task = await self._get_task_by_id(
                task_id, published=True, session=session
            )
            task_entity = original_task.get_entity()

            helper_entity_to_remove = next(
                (
                    helper_entity
                    for helper_entity in await task_entity.awaitable_attrs.helpers
                    if helper_entity.member_id == member_id
                ),
                None,
            )
            if not helper_entity_to_remove:
                raise ControllerNotFoundException("Helper is not on the task")

            helper_to_remove = await MemberPublicInfoDto.create(
                await helper_entity_to_remove.awaitable_attrs.member
            )

            session.delete(helper_entity_to_remove)
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Removed helper from task: %s, helper: %s, user: %s",
                updated_task.id,
                helper_to_remove.username,
                user.username,
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/RemoveHelper/{task_id}/Helper/{member_id}",
            )
            self._run_in_background(
                self._notifications.on_remove_helper(
                    updated_task, helper_to_remove, user
                )
            )

            return updated_task

    async def sign_up_as_captain(self, task_id: int, user: User) -> HelperTaskDto:
        with self.database_action(
            action="Helper Task / Sign Up As Captain",
            user=user,
            details={"task_id": task_id},
        ) as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)

            await self._check_can_sign_up_as_captain(
                task=task,
                member_id=user.member_id,
                editor_action=False,
                session=session,
            )
            task_entity = task.get_entity()
            task_entity.captain_id = user.member_id
            task_entity.captain_signed_up_at = get_now()
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Signed up as captain for task: %s, user: %s",
                updated_task.id,
                user.username,
            )

            self._audit_log(session, user, f"Helpers/Tasks/SignUpAsCaptain/{task_id}")
            self._run_in_background(self._notifications.on_sign_up(updated_task, user))

            return updated_task

    async def sign_up_as_helper(self, task_id: int, user: User) -> HelperTaskDto:
        with self.database_action(
            action="Helper Task / Sign Up As Helper",
            user=user,
            details={"task_id": task_id},
        ) as session:
            task = await self.get_task_by_id(task_id, published=True, session=session)

            await self._check_can_sign_up_as_helper(
                task=task,
                member_id=user.member_id,
                editor_action=False,
                session=session,
            )

            helper_entity = HelperTaskHelperEntity(
                task_id=task.id, member_id=user.member_id, signed_up_at=get_now()
            )
            session.add(helper_entity)
            session.commit()

            updated_task = await self.get_task_by_id(
                task_id, published=True, session=session
            )
            self._logger.info(
                "Signed up as helper for task: %s, user: %s",
                updated_task.id,
                user.username,
            )

            self._audit_log(session, user, f"Helpers/Tasks/SignUpAsHelper/{task_id}")
            self._run_in_background(self._notifications.on_sign_up(updated_task, user))

            return updated_task

    async def mark_as_done(
        self, task_id: int, request: HelperTaskMarkAsDoneRequestDto, user: User
    ) -> HelperTaskDto:
        with self.database_action(
            action="Helper Task / Mark As Done",
            user=user,
            details={"task_id": task_id, "request": request},
        ) as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)

            if task.state != HelperTaskState.PENDING:
                raise ControllerConflictException("Task already marked as done")
            if self._starts_in_the_future(task):
                raise ControllerConflictException(
                    "Cannot mark a task as done before it starts"
                )

            task_entity = task.get_entity()
            task_entity.marked_as_done_at = get_now()
            task_entity.marked_as_done_by_id = user.member_id
            task_entity.marked_as_done_comment = request.comment
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Marked task as done: %s, user: %s", updated_task.id, user.username
            )

            self._audit_log(session, user, f"Helpers/Tasks/MarkAsDone/{task_id}")
            self._run_in_background(
                self._notifications.on_mark_as_done(updated_task, user)
            )

            return updated_task

    async def validate(
        self, task_id: int, request: HelperTaskValidationRequestDto, user: User
    ) -> HelperTaskDto:
        with self.database_action(
            action="Helper Task / Validate",
            user=user,
            details={"task_id": task_id, "request": request},
        ) as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)

            if task.state == HelperTaskState.VALIDATED:
                raise ControllerConflictException("Task already validated")
            if self._starts_in_the_future(task):
                raise ControllerConflictException(
                    "Cannot validate a task before it starts"
                )

            task_entity = task.get_entity()
            now = get_now()

            if not task_entity.marked_as_done_at:
                task_entity.marked_as_done_at = now
                task_entity.marked_as_done_by_id = user.member_id

            task_entity.validated_at = now
            task_entity.validated_by_id = user.member_id
            task_entity.validation_comment = request.comment
            session.commit()

            updated_task = await HelperTaskDto.create(task_entity)
            self._logger.info(
                "Validated task: %s, user: %s",
                updated_task.id,
                user.username,
            )

            self._audit_log(
                session,
                user,
                f"Helpers/Tasks/Validate/{task_id}",
            )
            self._run_in_background(self._notifications.on_validate(updated_task, user))

            # Do it before the requests finishes, so the next request gets the updated state
            await self._unset_urgent_for_validated_tasks(user=user, session=session)

            return updated_task

    async def _unset_urgent_for_validated_tasks(
        self, *, user: User, session: Session
    ) -> None:
        validated_urgent_tasks = (
            session.scalars(
                select(HelperTaskEntity).where(
                    HelperTaskEntity.validated_by_id.is_not(None),
                    # Need == 1 instead of True for Oracle
                    HelperTaskEntity.urgent == 1,
                )
            )
            .unique()
            .all()
        )

        for task in validated_urgent_tasks:
            task.urgent = False

        session.commit()

        self._logger.info(
            "Unset urgent for %d validated task(s)", len(validated_urgent_tasks)
        )

        for task in validated_urgent_tasks:
            self._audit_log(
                session, user, f"Helpers/Tasks/UnsetUrgentForValidatedTask/{task.id}"
            )

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
        if not CONFIG.emails_enabled(self._logger):
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

        with self.database_action(
            action="Helpers / Send Daily Reminders",
            user=None,
            details=None,
        ) as session:
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
                    self._logger.warning("Task %s has no timing information", task.id)
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
                    # Shifts: skip reminder if timing_latest is more recent (greater) than one week ago
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

    async def _check_can_sign_up_as_captain(
        self,
        *,
        task: HelperTaskDto,
        member_id: int,
        editor_action: bool,
        session: Session,
    ) -> None:
        await self._check_can_sign_up(
            task=task, member_id=member_id, editor_action=editor_action
        )

        if task.captain:
            raise ControllerConflictException("Task already has a captain")

        if task.captain_required_licence_info:
            has_licence = (
                session.scalar(
                    select(LicenceEntity).where(
                        LicenceEntity.member_id == member_id,
                        LicenceEntity.licence_id
                        == task.captain_required_licence_info.id,
                        LicenceEntity.status > 0,
                    )
                )
                is not None
            )

            if not has_licence:
                raise ControllerConflictException(
                    f"Task captain needs licence: {task.captain_required_licence_info.licence}"
                )

    async def _check_can_sign_up_as_helper(
        self,
        *,
        task: HelperTaskDto,
        member_id: int,
        editor_action: bool,
        session: Session,
    ) -> None:
        await self._check_can_sign_up(
            task=task, member_id=member_id, editor_action=editor_action
        )

        if len(task.helpers) >= task.helper_max_count:
            raise ControllerConflictException("Task helper limit reached")

        if not editor_action:
            # Check: helper cannot sign up for multiple surveillance tasks before mid-June:
            # 1. This allows more members completing one surveillance shift in the beginning of the season
            # 2. Members who want to do all their tasks early can still do maintenance tasks

            surveillance_task = "surveillance" in task.category.title.lower()
            mid_june = date(task.year, 6, 15)
            message = "You cannot sign up for multiple surveillance shifts before mid-June — but you can still sign up for maintenance tasks!"

            if (
                surveillance_task
                and task.starts_at
                and task.starts_at.date() < mid_june
            ):
                # Check if the member has signed up for any other surveillance shift before mid-June
                other_tasks = await self._find_tasks(
                    year=task.year,
                    task_id=None,
                    published=None,
                    where=and_(
                        # Assumes that we only have one surveillance category, good enough
                        HelperTaskEntity.category_id == task.category.id,
                        HelperTaskEntity.starts_at < mid_june,
                        or_(
                            HelperTaskEntity.helpers.any(
                                HelperTaskHelperEntity.member_id == member_id
                            ),
                        ),
                    ),
                    session=session,
                )
                if other_tasks:
                    raise ControllerConflictException(message)

    async def _check_can_sign_up(
        self, *, task: HelperTaskDto, member_id: int, editor_action: bool
    ) -> None:
        if not task.published:
            raise ControllerConflictException("Cannot sign up for an unpublished task")

        if not editor_action:
            if task.state == HelperTaskState.DONE:
                raise ControllerConflictException(
                    "Cannot sign up for a task marked as done"
                )
            if task.state == HelperTaskState.VALIDATED:
                raise ControllerConflictException("Cannot sign up for a validated task")

            now = get_now()
            if (task.starts_at and task.starts_at < now) or (
                task.deadline and task.deadline < now
            ):
                raise ControllerConflictException(
                    "Cannot sign up for a task in the past"
                )

        if task.captain and task.captain.member.id == member_id:
            raise ControllerConflictException("Already signed up as captain")
        if any(helper.member.id == member_id for helper in task.helpers):
            raise ControllerConflictException("Already signed up as helper")

    def _starts_in_the_future(self, task: HelperTaskDto) -> bool:
        return bool(task.starts_at and task.starts_at > get_now())
