"""
Holiday API endpoints.
"""
from typing import Sequence

from fastapi import APIRouter

from ycc_hull.controllers.holidays_controller import HolidaysController
from ycc_hull.models.dtos import HolidayDto

api_holidays = APIRouter()


@api_holidays.get("/api/v0/holidays")
async def holidays_get() -> Sequence[HolidayDto]:
    return await HolidaysController.find_all()
