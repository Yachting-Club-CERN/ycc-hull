"""
Licences controller.
"""
from collections.abc import Sequence
from sqlalchemy import select
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.db.entities import LicenceInfoEntity
from ycc_hull.models.dtos import LicenceDetailedInfoDto


class LicencesController(BaseController):
    """
    Licences controller. Returns DTO objects.
    """

    async def find_all_licence_infos(self) -> Sequence[LicenceDetailedInfoDto]:
        return self.database_context.query_all(
            select(LicenceInfoEntity).order_by(LicenceInfoEntity.nlicence),
            LicenceDetailedInfoDto.create,
        )
