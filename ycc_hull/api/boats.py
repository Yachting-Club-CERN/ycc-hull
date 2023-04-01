"""
Boat API endpoints.
"""
from typing import Sequence

from fastapi import APIRouter

from ycc_hull.controllers.boats_controller import BoatsController
from ycc_hull.models.dtos import BoatDto

api_boats = APIRouter()


@api_boats.get("/api/v0/boats")
async def boats_get() -> Sequence[BoatDto]:
    return await BoatsController.find_all()
