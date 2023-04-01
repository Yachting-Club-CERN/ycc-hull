"""
General controllers.
"""
from typing import Sequence

from sqlalchemy import select

from ycc_hull.db.engine import query_all
from ycc_hull.db.entities import HolidayEntity
from ycc_hull.models.dtos import HolidayDto


class HolidaysController:
    """
    Holidays controller. Returns DTO objects.
    """

    @staticmethod
    async def find_all() -> Sequence[HolidayDto]:
        return query_all(
            select(HolidayEntity).order_by(HolidayEntity.day), HolidayDto.create
        )
