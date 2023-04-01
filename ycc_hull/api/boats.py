"""
Boat API endpoints.
"""
from typing import Sequence

from fastapi import APIRouter, Depends
from ycc_hull.auth import auth

from ycc_hull.controllers.boats_controller import BoatsController
from ycc_hull.models.dtos import BoatDto

api_boats = APIRouter(dependencies=[Depends(auth)])


@api_boats.get("/api/v0/boats")
async def boats_get() -> Sequence[BoatDto]:
    return await BoatsController.find_all()
