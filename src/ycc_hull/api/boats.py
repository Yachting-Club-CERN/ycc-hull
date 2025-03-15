"""
Boat API endpoints.
"""

from collections.abc import Sequence
from fastapi import APIRouter, Depends
from ycc_hull.auth import auth

from ycc_hull.controllers.boats_controller import BoatsController
from ycc_hull.models.dtos import BoatDto

api_boats = APIRouter(dependencies=[Depends(auth)])
controller = BoatsController()


@api_boats.get("/api/v1/boats")
async def boats_get() -> Sequence[BoatDto]:
    return await controller.find_all()
