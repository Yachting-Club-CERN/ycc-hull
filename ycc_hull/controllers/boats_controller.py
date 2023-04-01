"""
Boats controller.
"""
from typing import Sequence
from sqlalchemy import select
from ycc_hull.db.engine import query_all
from ycc_hull.db.entities import BoatEntity
from ycc_hull.models.dtos import BoatDto


class BoatsController:
    """
    Boats controller. Returns DTO objects.
    """

    @staticmethod
    async def find_all() -> Sequence[BoatDto]:
        return query_all(
            select(BoatEntity).order_by(BoatEntity.table_pos), BoatDto.create
        )
