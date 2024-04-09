"""
Holidays controller.
"""

from collections.abc import Sequence

from sqlalchemy import select
from ycc_hull.controllers.base_controller import BaseController

from ycc_hull.db.entities import HolidayEntity
from ycc_hull.models.dtos import HolidayDto


class HolidaysController(BaseController):
    """
    Holidays controller. Returns DTO objects.
    """

    async def find_all(self) -> Sequence[HolidayDto]:
        return await self.database_context.query_all(
            select(HolidayEntity).order_by(HolidayEntity.day),
            async_transformer=HolidayDto.create,
        )
