"""
Helpers controller.
"""
from collections.abc import Sequence
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session, lazyload

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
        return self.database_context.query_all(
            select(HelperTaskCategoryEntity).order_by(HelperTaskCategoryEntity.title),
            HelperTaskCategoryDto.create,
        )

    async def find_all_tasks(
        self,
        published: Optional[bool] = None,
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
        with self.database_context.create_session() as session:
            try:
                task_entity = HelperTaskEntity(**task_mutation_request.dict())
                session.add(task_entity)
                session.commit()

                task = HelperTaskDto.create(task_entity)
                self._logger.info("Created task: %s, user: %s", task, user)

                session.add(
                    create_audit_entry(user, "Helpers/Tasks/Create", {"new": task})
                )
                session.commit()

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
        with self.database_context.create_session() as session:
            old_task = await self._get_task_by_id(task_id, session=session)

            # Check: cannot change timing if anyone has subscribed
            if old_task.captain or old_task.helpers:
                if (
                    task_mutation_request.start != old_task.start
                    or task_mutation_request.end != old_task.end
                    or task_mutation_request.deadline != old_task.deadline
                ):
                    raise ControllerConflictException(
                        "Cannot change timing after anyone has subscribed"
                    )
                if not task_mutation_request.published:
                    raise ControllerConflictException(
                        "You must publish a task after anyone has subscribed"
                    )

            # Check: if a captain has subscribed then the new licence must be active for the captain
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
                        "Cannot change captain required licence info because the subscribed captain does not have the newly specified licence"
                    )

            # Check: cannot decrease helpers maximum count below subscribed helpers count
            if task_mutation_request.helpers_max_count < len(old_task.helpers):
                raise ControllerConflictException(
                    "Cannot decrease helpers maximum count below subscribed helpers count"
                )

            try:
                task_entity = old_task.get_entity()
                old_task = HelperTaskDto.create(task_entity)
                self._update_entity_from_dto(task_entity, task_mutation_request)
                session.commit()

                new_task = HelperTaskDto.create(task_entity)
                self._logger.info("Created task: %s, user: %s", old_task, user)

                session.add(
                    create_audit_entry(
                        user,
                        f"Helpers/Tasks/Update/{task_id}",
                        {"old": old_task, "new": new_task},
                    )
                )
                session.commit()

                return new_task
            except DatabaseError as exc:
                raise self._handle_database_error(  # pylint: disable=raising-bad-type
                    exc, "update task", user, task_mutation_request
                )

    async def subscribe_as_captain(self, task_id: int, user: User) -> None:
        with self.database_context.create_session() as session:
            task = await self._get_task_by_id(task_id, published=True, session=session)

            await self._check_can_subscribe(task, user.member_id)
            if task.captain:
                raise ControllerConflictException("Task already has a captain")

            if task.captain_required_licence_info:
                required_licence = task.captain_required_licence_info.licence
                if not user.has_licence(required_licence):
                    raise ControllerConflictException(
                        f"Task captain needs licence: {required_licence}"
                    )

            task_entity = session.scalars(
                select(HelperTaskEntity)
                .options(lazyload("*"))
                .where(HelperTaskEntity.id == task_id)
            ).one()
            task_entity.captain_id = user.member_id
            task_entity.captain_subscribed_at = datetime.now()
            session.add(
                create_audit_entry(user, f"Helpers/Tasks/SubscribeAsCaptain/{task_id}")
            )
            session.commit()

    async def subscribe_as_helper(self, task_id: int, user: User) -> None:
        task = await self.get_task_by_id(task_id, published=True)

        await self._check_can_subscribe(task, user.member_id)
        if len(task.helpers) >= task.helpers_max_count:
            raise ControllerConflictException("Task helper limit reached")

        with self.database_context.create_session() as session:
            helper = HelperTaskHelperEntity(
                task_id=task.id, member_id=user.member_id, subscribed_at=datetime.now()
            )
            session.add(helper)
            session.add(
                create_audit_entry(user, f"Helpers/Tasks/SubscribeAsHelper/{task_id}")
            )
            session.commit()

    async def _find_tasks(
        self,
        task_id: Optional[int],
        published: Optional[bool],
        session: Optional[Session] = None,
    ) -> Sequence[HelperTaskDto]:
        query = select(HelperTaskEntity)

        if task_id is not None:
            query = query.where(HelperTaskEntity.id == task_id)
        if published is not None:
            query = query.where(HelperTaskEntity.published == published)

        query = query.order_by(
            HelperTaskEntity.urgent.desc(),
            func.coalesce(  # pylint: disable=not-callable
                HelperTaskEntity.start, HelperTaskEntity.deadline
            ).asc(),
        )

        return self.database_context.query_all(
            query,
            HelperTaskDto.create,
            unique=True,
            session=session,
        )

    async def _find_task_by_id(
        self, task_id: int, published: Optional[bool], session: Optional[Session] = None
    ) -> Optional[HelperTaskDto]:
        tasks = await self._find_tasks(task_id, published, session=session)
        return tasks[0] if tasks else None

    async def _get_task_by_id(
        self,
        task_id: int,
        published: Optional[bool] = None,
        session: Optional[Session] = None,
    ) -> HelperTaskDto:
        task = await self._find_task_by_id(task_id, published, session=session)
        if task:
            return task
        raise ControllerNotFoundException("Task not found")

    async def _check_can_subscribe(self, task: HelperTaskDto, member_id: int) -> None:
        if not task.published:
            raise ControllerConflictException("Cannot subscribe to an unpublished task")

        now = datetime.now()
        if (task.start and task.start < now) or (task.deadline and task.deadline < now):
            raise ControllerConflictException("Cannot subscribe to a task in the past")

        if task.captain and task.captain.member.id == member_id:
            raise ControllerConflictException("Already subscribed as captain")
        if any(helper.member.id == member_id for helper in task.helpers):
            raise ControllerConflictException("Already subscribed as helper")
