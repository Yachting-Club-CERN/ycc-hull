"""
Test Data API endpoints.
"""
from fastapi import APIRouter
from test_data.controllers.test_data_controller import TestDataController


# No auth needed for local development
api_test_data = APIRouter()
controller = TestDataController()


@api_test_data.post("/api/v1/test-data/populate")
async def populate() -> list[str]:
    return await controller.populate()


@api_test_data.post("/api/v1/test-data/clear")
async def clear() -> list[str]:
    return await controller.clear()


@api_test_data.post("/api/v1/test-data/repopulate")
async def repopulate() -> list[str]:
    return await controller.repopulate()
