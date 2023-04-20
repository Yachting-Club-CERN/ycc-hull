"""
Licence API endpoints.
"""
from collections.abc import Sequence
from fastapi import APIRouter, Depends
from ycc_hull.auth import auth

from ycc_hull.controllers.licences_controller import LicencesController
from ycc_hull.models.dtos import LicenceDetailedInfoDto

api_licences = APIRouter(dependencies=[Depends(auth)])
controller = LicencesController()


@api_licences.get("/api/v0/licence-infos")
async def licence_infos_get() -> Sequence[LicenceDetailedInfoDto]:
    return await controller.find_all_licence_infos()
