"""
Helpers controller.
"""
from datetime import datetime
from typing import Optional, Sequence, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, lazyload

from ycc_hull.controllers.exceptions import (
    ControllerConflictException,
    ControllerNotFoundException,
)
from ycc_hull.db.engine import get_db_engine, query_all
from ycc_hull.db.entities import (
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
)
from ycc_hull.models.helpers_dtos import HelperTaskCategoryDto, HelperTaskDto


class HelpersController:
    """
    Helpers controller. Returns DTO objects.
    """

    @staticmethod
    async def find_all_task_categories() -> Sequence[HelperTaskCategoryDto]:
        return query_all(
            select(HelperTaskCategoryEntity).order_by(HelperTaskCategoryEntity.title),
            HelperTaskCategoryDto.create,
        )

    @classmethod
    async def find_all_tasks(
        cls,
        published: Optional[bool] = None,
    ) -> Sequence[HelperTaskDto]:
        return await cls._find_tasks(None, published)

    @classmethod
    async def find_task_by_id(
        cls, task_id: int, published: Optional[bool] = None
    ) -> Optional[HelperTaskDto]:
        tasks = await cls._find_tasks(task_id, published)
        return tasks[0] if tasks else None

    @classmethod
    async def get_task_by_id(
        cls, task_id: int, published: Optional[bool] = None
    ) -> HelperTaskDto:
        task = await cls.find_task_by_id(task_id, published)
        if task:
            return task
        raise ControllerNotFoundException("Task not found")

    @classmethod
    async def subscribe_as_captain(
        cls, task_id: int, member_id: int, member_roles: Tuple[str]
    ) -> None:
        task = await cls.get_task_by_id(task_id, published=True)

        await cls._check_can_subscribe(task, member_id)
        if task.captain:
            raise ControllerConflictException("Task already has a captain")

        if task.captain_required_licence:
            required_licence = task.captain_required_licence.licence
            if f"ycc-licence-{required_licence.lower()}" not in member_roles:
                raise ControllerConflictException(
                    f"Task captain needs licence: {required_licence}"
                )

        with Session(get_db_engine()) as session:
            task_entity = session.scalars(
                select(HelperTaskEntity)
                .options(lazyload("*"))
                .where(HelperTaskEntity.id == task_id)
            ).one()
            task_entity.captain_id = member_id
            task_entity.captain_subscribed_at = datetime.now()
            session.commit()

    @classmethod
    async def subscribe_as_helper(cls, task_id: int, member_id: int) -> None:
        task = await cls.get_task_by_id(task_id, published=True)

        await cls._check_can_subscribe(task, member_id)
        if len(task.helpers) >= task.helpers_max_count:
            raise ControllerConflictException("Task helper limit reached")

        with Session(get_db_engine()) as session:
            helper = HelperTaskHelperEntity(
                task_id=task.id, member_id=member_id, subscribed_at=datetime.now()
            )
            session.add(helper)
            session.commit()

    @staticmethod
    async def _find_tasks(
        task_id: Optional[int], published: Optional[bool]
    ) -> Sequence[HelperTaskDto]:
        query = select(HelperTaskEntity).options(joinedload(HelperTaskEntity.category))

        if task_id is not None:
            query = query.where(HelperTaskEntity.id == task_id)
        if published is not None:
            query = query.where(HelperTaskEntity.published == published)

        query = query.order_by(
            func.coalesce(  # pylint: disable=not-callable
                HelperTaskEntity.start, HelperTaskEntity.deadline
            ).desc()
        )

        return query_all(
            query,
            HelperTaskDto.create,
            unique=True,
        )

    @staticmethod
    async def _check_can_subscribe(task: HelperTaskDto, member_id: int) -> None:
        now = datetime.now()
        if (task.start and task.start < now) or (task.deadline and task.deadline < now):
            raise ControllerConflictException("Cannot subscribe to a task in the past")

        if task.captain and task.captain.member.id == member_id:
            raise ControllerConflictException("Already subscribed as captain")
        if any(helper.member.id == member_id for helper in task.helpers):
            raise ControllerConflictException("Already subscribed as helper")
