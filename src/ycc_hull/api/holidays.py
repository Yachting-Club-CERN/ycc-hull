"""Holiday API endpoints."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends

from ycc_hull.app_controllers import get_holidays_controller
from ycc_hull.auth import auth
from ycc_hull.controllers.holidays_controller import HolidaysController
from ycc_hull.models.dtos import HolidayDto

api_holidays = APIRouter(dependencies=[Depends(auth)])


@api_holidays.get("/api/v1/holidays")
async def holidays_get(
    controller: Annotated[HolidaysController, Depends(get_holidays_controller)],
) -> Sequence[HolidayDto]:
    """List all holidays."""
    return await controller.find_all()
