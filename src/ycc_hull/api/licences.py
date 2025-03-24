"""
Licence API endpoints.
"""

from collections.abc import Sequence

from fastapi import APIRouter, Depends

from ycc_hull.app_controllers import get_licences_controller
from ycc_hull.auth import auth
from ycc_hull.controllers.licences_controller import LicencesController
from ycc_hull.models.dtos import LicenceDetailedInfoDto

api_licences = APIRouter(dependencies=[Depends(auth)])


@api_licences.get("/api/v1/licence-infos")
async def licence_infos_get(
    controller: LicencesController = Depends(get_licences_controller),
) -> Sequence[LicenceDetailedInfoDto]:
    return await controller.find_all_licence_infos()
