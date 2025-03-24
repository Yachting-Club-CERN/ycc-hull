"""
Test Data API endpoints.
"""

from fastapi import APIRouter, Depends, Query

from test_data.controllers.test_data_controller import TestDataController

# No auth needed for local development
api_test_data = APIRouter()
controller = TestDataController()


def _get_add_daily_helper_tasks(
    add_daily_helper_tasks: bool = Query(
        False,
        description="If true, daily helper tasks will also be created. This is useful if you need a lot of tasks for testing.",
    )
) -> bool:
    return add_daily_helper_tasks


@api_test_data.post("/api/v1/test-data/populate")
async def populate(
    add_daily_helper_tasks: bool = Depends(_get_add_daily_helper_tasks),
) -> list[str]:
    return await controller.populate(add_daily_helper_tasks)


@api_test_data.post("/api/v1/test-data/clear")
async def clear() -> list[str]:
    return await controller.clear()


@api_test_data.post("/api/v1/test-data/repopulate")
async def repopulate(
    add_daily_helper_tasks: bool = Depends(_get_add_daily_helper_tasks),
) -> list[str]:
    return await controller.repopulate(add_daily_helper_tasks)
