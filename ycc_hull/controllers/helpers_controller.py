"""
Helpers controller.
"""
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import and_, func, select
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
    LicenceEntity,
    LicenceInfoEntity,
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

    @staticmethod
    async def find_all_tasks(
        published: Optional[bool] = None,
    ) -> Sequence[HelperTaskDto]:
        return await __class__._find_tasks(None, published)

    @staticmethod
    async def find_task_by_id(
        task_id: int, published: Optional[bool] = None
    ) -> Optional[HelperTaskDto]:
        tasks = await __class__._find_tasks(task_id, published)
        return tasks[0] if tasks else None

    @staticmethod
    async def get_task_by_id(
        task_id: int, published: Optional[bool] = None
    ) -> HelperTaskDto:
        task = await __class__.find_task_by_id(task_id, published)
        if task:
            return task
        else:
            raise ControllerNotFoundException("Task not found")

    @staticmethod
    async def subscribe_as_captain(task_id: int, member_id: int) -> None:
        task = await __class__.get_task_by_id(task_id, published=True)

        # TODO check cannot subscribe to task with deadline/start in the past
        await __class__._check_not_already_subscribed(task, member_id)
        if task.captain:
            raise ControllerConflictException("Task already has a captain")

        with Session(get_db_engine()) as session:
            # Check licence
            if (
                task.captain_required_licence
                and session.scalar(
                    select(func.count())
                    .select_from(LicenceEntity)
                    .where(
                        and_(
                            LicenceEntity.member_id == member_id,
                            LicenceEntity.status > 0,
                            LicenceEntity.licence_id
                            == task.captain_required_licence.id,
                        )
                    )
                )
                < 1
            ):
                raise ControllerConflictException(
                    "Task captain needs licence: "
                    + task.captain_required_licence.licence
                )

            # Subscribe
            task_entity = session.scalars(
                select(HelperTaskEntity)
                .options(lazyload("*"))
                .where(HelperTaskEntity.id == task_id)
            ).one()
            task_entity.captain_id = member_id
            task_entity.captain_subscribed_at = datetime.now()
            session.commit()

    @staticmethod
    async def subscribe_as_helper(task_id: int, member_id: int) -> None:
        task = await __class__.get_task_by_id(task_id, published=True)

        # TODO check cannot subscribe to task with deadline/start in the past
        await __class__._check_not_already_subscribed(task, member_id)
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
    async def _check_not_already_subscribed(
        task: HelperTaskDto, member_id: int
    ) -> None:
        if task.captain and task.captain.member.id == member_id:
            raise ControllerConflictException("Already subscribed as captain")
        if any(helper.member.id == member_id for helper in task.helpers):
            raise ControllerConflictException("Already subscribed as helper")
