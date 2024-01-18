"""
Holiday API endpoints.
"""
from collections.abc import Sequence

from fastapi import APIRouter, Depends

from ycc_hull.auth import auth
from ycc_hull.controllers.holidays_controller import HolidaysController
from ycc_hull.models.dtos import HolidayDto

api_holidays = APIRouter(dependencies=[Depends(auth)])
controller = HolidaysController()


@api_holidays.get("/api/v1/holidays")
async def holidays_get() -> Sequence[HolidayDto]:
    return await controller.find_all()
