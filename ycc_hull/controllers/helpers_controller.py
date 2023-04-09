"""
Helpers controller.
"""
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from ycc_hull.db.engine import query_all
from ycc_hull.db.entities import (
    HelperTaskCategoryEntity,
    HelperTaskEntity,
)
from ycc_hull.models.helpers_dtos import (
    HelperTaskCategoryDto,
    HelperTaskDto,
)


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
