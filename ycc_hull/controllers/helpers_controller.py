"""
Helpers controller.
"""
from collections.abc import Sequence
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, lazyload

from ycc_hull.controllers.audit import create_audit_entry
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.exceptions import (
    ControllerConflictException,
    ControllerNotFoundException,
)
from ycc_hull.db.entities import (
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
)
from ycc_hull.models.helpers_dtos import (
    HelperTaskCategoryDto,
    HelperTaskDto,
    HelperTaskMutationRequestDto,
)
from ycc_hull.models.user import User


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
        self, published: Optional[bool] = None
    ) -> Sequence[HelperTaskDto]:
        return await self._find_tasks(None, published)

    async def find_task_by_id(
        self, task_id: int, published: Optional[bool] = None
    ) -> Optional[HelperTaskDto]:
        return await self._find_task_by_id(task_id, published)

    async def get_task_by_id(
        self, task_id: int, published: Optional[bool] = None
    ) -> HelperTaskDto:
        task = await self.find_task_by_id(task_id, published)
        if task:
            return task
        raise ControllerNotFoundException("Task not found")

    async def create_task(
        self, task_mutation_request: HelperTaskMutationRequestDto, user: User
    ) -> HelperTaskDto:
        async with self.database_context.async_session() as session:
            try:
                task_entity = HelperTaskEntity(**task_mutation_request.model_dump())
                session.add(task_entity)
                await session.commit()

                task = await HelperTaskDto.create(task_entity)
                self._logger.info("Created task: %s, user: %s", task, user)

                session.add(
                    create_audit_entry(user, "Helpers/Tasks/Create", {"new": task})
                )
                await session.commit()

                return task
            except DatabaseError as exc:
                raise self._handle_database_error(  # pylint: disable=raising-bad-type
                    exc, "create task", user, task_mutation_request
                )

    async def update_task(
        self,
        task_id: int,
        task_mutation_request: HelperTaskMutationRequestDto,
        user: User,
    ) -> HelperTaskDto:
        async with self.database_context.async_session() as session:
            old_task = await self._get_task_by_id(task_id, session=session)

            # Check: cannot change timing if anyone has signed up
            if old_task.captain or old_task.helpers:
                if (
                    task_mutation_request.starts_at != old_task.starts_at
                    or task_mutation_request.ends_at != old_task.ends_at
                    or task_mutation_request.deadline != old_task.deadline
                ):
                    raise ControllerConflictException(
                        "Cannot change timing after anyone has signed up"
                    )
                if not task_mutation_request.published:
                    raise ControllerConflictException(
                        "You must publish a task after anyone has signed up"
                    )

            # Check: if a captain has signed up then the new licence must be active for the captain
            if (
                old_task.captain
                and task_mutation_request.captain_required_licence_info_id
                != (
                    old_task.captain_required_licence_info.id
                    if old_task.captain_required_licence_info
                    else None
                )
            ):
                captain_entity = old_task.captain.member.get_entity()
                if not any(
                    licence_info_entity.infoid
                    == task_mutation_request.captain_required_licence_info_id
                    for licence_info_entity in captain_entity.active_licence_infos
                ):
                    raise ControllerConflictException(
                        "Cannot change captain required licence info because the signed up captain does not have the newly specified licence"
                    )

            # Check: cannot decrease helpers maximum count below signed up helpers count
            if task_mutation_request.helper_max_count < len(old_task.helpers):
                raise ControllerConflictException(
                    "Cannot decrease helpers maximum count below signed up helpers count"
                )

            try:
                task_entity = old_task.get_entity()
                old_task = await HelperTaskDto.create(task_entity)
                self._update_entity_from_dto(task_entity, task_mutation_request)
                await session.commit()

                new_task = await HelperTaskDto.create(task_entity)
                self._logger.info("Updated task: %s, user: %s", new_task, user)

                session.add(
                    create_audit_entry(
                        user,
                        f"Helpers/Tasks/Update/{task_id}",
                        {"old": old_task, "new": new_task},
                    )
                )
                await session.commit()

                return new_task
            except DatabaseError as exc:
                raise self._handle_database_error(  # pylint: disable=raising-bad-type
                    exc, "update task", user, task_mutation_request
                )

    async def sign_up_as_captain(self, task_id: int, user: User) -> None:
        async with self.database_context.async_session() as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)

            await self._check_can_sign_up(task, user.member_id)
            if task.captain:
                raise ControllerConflictException("Task already has a captain")

            if task.captain_required_licence_info:
                required_licence = task.captain_required_licence_info.licence
                if not user.has_licence(required_licence):
                    raise ControllerConflictException(
                        f"Task captain needs licence: {required_licence}"
                    )

            task_entity = (
                await session.scalars(
                    select(HelperTaskEntity)
                    .options(lazyload("*"))
                    .where(HelperTaskEntity.id == task_id)
                )
            ).one()
            task_entity.captain_id = user.member_id
            task_entity.captain_signed_up_at = datetime.now()
            await session.commit()

            session.add(
                create_audit_entry(user, f"Helpers/Tasks/SignUpAsCaptain/{task_id}")
            )
            await session.commit()

    async def sign_up_as_helper(self, task_id: int, user: User) -> None:
        task = await self.get_task_by_id(task_id, published=True)

        await self._check_can_sign_up(task, user.member_id)
        if len(task.helpers) >= task.helper_max_count:
            raise ControllerConflictException("Task helper limit reached")

        async with self.database_context.async_session() as session:
            helper = HelperTaskHelperEntity(
                task_id=task.id, member_id=user.member_id, signed_up_at=datetime.now()
            )
            session.add(helper)
            await session.commit()

            session.add(
                create_audit_entry(user, f"Helpers/Tasks/SignUpAsHelper/{task_id}")
            )
            await session.commit()

    async def _find_tasks(
        self,
        task_id: Optional[int],
        published: Optional[bool],
        session: Optional[AsyncSession] = None,
    ) -> Sequence[HelperTaskDto]:
        query = select(HelperTaskEntity)

        exclude_long_description: bool = task_id is None

        if exclude_long_description:
            query = query.options(
                defer(HelperTaskEntity.long_description, raiseload=True)
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
            async_transformer=HelperTaskDto.create_without_long_description
            if exclude_long_description
            else HelperTaskDto.create,
            unique=True,
            session=session,
        )

    async def _find_task_by_id(
        self,
        task_id: int,
        published: Optional[bool],
        session: Optional[AsyncSession] = None,
    ) -> Optional[HelperTaskDto]:
        tasks = await self._find_tasks(task_id, published, session=session)
        return tasks[0] if tasks else None

    async def _get_task_by_id(
        self,
        task_id: int,
        published: Optional[bool] = None,
        session: Optional[AsyncSession] = None,
    ) -> HelperTaskDto:
        task = await self._find_task_by_id(task_id, published, session=session)
        if task:
            return task
        raise ControllerNotFoundException("Task not found")

    async def _check_can_sign_up(self, task: HelperTaskDto, member_id: int) -> None:
        if not task.published:
            raise ControllerConflictException("Cannot sign up to an unpublished task")

        now = datetime.now()
        if (task.starts_at and task.starts_at < now) or (
            task.deadline and task.deadline < now
        ):
            raise ControllerConflictException("Cannot sign up to a task in the past")

        if task.captain and task.captain.member.id == member_id:
            raise ControllerConflictException("Already signed up as captain")
        if any(helper.member.id == member_id for helper in task.helpers):
            raise ControllerConflictException("Already signed up as helper")
