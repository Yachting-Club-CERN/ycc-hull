"""
Helpers controller.
"""
from typing import Sequence

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
    async def find_all_tasks() -> Sequence[HelperTaskDto]:
        # TODO Handle the published flag
        return query_all(
            select(HelperTaskEntity)
            .options(joinedload(HelperTaskEntity.category))
            .order_by(
                func.coalesce(  # pylint: disable=not-callable
                    HelperTaskEntity.start, HelperTaskEntity.deadline
                ).desc()
            ),
            HelperTaskDto.create,
            unique=True,
        )
