"""
Boats controller.
"""
from collections.abc import Sequence
from sqlalchemy import select
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.db.entities import BoatEntity
from ycc_hull.models.dtos import BoatDto


class BoatsController(BaseController):
    """
    Boats controller. Returns DTO objects.
    """

    async def find_all(self) -> Sequence[BoatDto]:
        return await self.database_context.query_all(
            select(BoatEntity).order_by(BoatEntity.table_pos),
            async_transformer=BoatDto.create,
        )
