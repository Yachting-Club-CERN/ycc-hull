"""
Helpers controller.
"""
from collections.abc import Sequence
from datetime import datetime
import logging
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import lazyload

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
    HelperTaskCreationRequestDto,
    HelperTaskDto,
)
from ycc_hull.models.user import User

logger = logging.getLogger(__name__)


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
        tasks = await self._find_tasks(task_id, published)
        return tasks[0] if tasks else None

    async def get_task_by_id(
        self, task_id: int, published: Optional[bool] = None
    ) -> HelperTaskDto:
        task = await self.find_task_by_id(task_id, published)
        if task:
            return task
        raise ControllerNotFoundException("Task not found")

    async def subscribe_as_captain(self, task_id: int, user: User) -> None:
        task = await self.get_task_by_id(task_id, published=True)

        await self._check_can_subscribe(task, user.member_id)
        if task.captain:
            raise ControllerConflictException("Task already has a captain")

        if task.captain_required_licence_info:
            required_licence = task.captain_required_licence_info.licence
            if not user.has_licence(required_licence):
                raise ControllerConflictException(
                    f"Task captain needs licence: {required_licence}"
                )

        with self.database_context.create_session() as session:
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

    async def create_task(
        self, task_creation_request: HelperTaskCreationRequestDto, user: User
    ) -> HelperTaskDto:
        with self.database_context.create_session() as session:
            try:
                task = HelperTaskEntity(**task_creation_request.dict())
                session.add(task)
                session.add(
                    create_audit_entry(user, "Helpers/Tasks/Create", {"new": task})
                )
                session.commit()
                created_task = HelperTaskDto.create(task)
                logger.info("Created task: %s, user: %s", created_task, user)
                return created_task
            except IntegrityError as exc:
                logger.info(
                    "Failed to create task: %s, user: %s, task_creation_request: %s",
                    exc,
                    user,
                    task_creation_request,
                )
                message = str(exc)

                user_message = None
                if "violated - parent key not found" in message:
                    if "HELPER_TASKS_CATEGORY_FK" in message:
                        user_message = "Invalid category"
                    if "HELPER_TASKS_CONTACT_FK" in message:
                        user_message = "Invalid contact"
                    if "HELPER_TASKS_CAPTAIN_REQUIRED_LICENCE_INFO_FK" in message:
                        user_message = "Invalid captain required licence info"

                if user_message:
                    raise ControllerConflictException(  # pylint: disable=raise-missing-from
                        user_message
                    )

                raise exc

    async def _find_tasks(
        self, task_id: Optional[int], published: Optional[bool]
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
        )

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
