"""
Helpers controller.
"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, defer, lazyload

from ycc_hull.controllers.audit import create_audit_entry
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.exceptions import (
    ControllerConflictException,
    ControllerNotFoundException,
)
from ycc_hull.controllers.notifications.notifications_controller import (
    send_helper_task_helper_sign_up_confirmation,
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
    HelperTaskUpdateRequestDto,
    HelperTaskValidationRequestDto,
)
from ycc_hull.models.user import User
from ycc_hull.utils import get_now


class HelpersController(BaseController):
    """
    Helpers controller. Returns DTO objects.
    """

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

                session.add(
                    create_audit_entry(user, "Helpers/Tasks/Create", {"new": task})
                )
                session.commit()

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

                session.add(
                    create_audit_entry(
                        user,
                        f"Helpers/Tasks/Update/{task_id}",
                        {"old": old_task, "new": new_task},
                    )
                )
                session.commit()

                if request.notify_participants:
                    pass
                    # TODO

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

            session.add(
                create_audit_entry(user, f"Helpers/Tasks/SignUpAsCaptain/{task_id}")
            )
            session.commit()

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
            # TODO only here for testing
            # await send_helper_task_helper_sign_up_confirmation(task, helper.member)
            # await send_helper_task_helper_sign_up_confirmation(task, task.contact)
            session.commit()

            session.add(
                create_audit_entry(user, f"Helpers/Tasks/SignUpAsHelper/{task_id}")
            )
            session.commit()

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

            session.add(
                create_audit_entry(
                    user, f"Helpers/Tasks/MarkAsDone/{task_id}", {"request": request}
                )
            )
            session.commit()

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

            session.add(
                create_audit_entry(
                    user,
                    f"Helpers/Tasks/Validate/{task_id}",
                    {"request": request},
                )
            )
            session.commit()

    async def _find_tasks(
        self,
        *,
        year: int | None,
        task_id: int | None,
        published: bool | None,
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
