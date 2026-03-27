"""Shared fixtures for API integration tests."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from tests.main_test import app_test, init_test_database
from ycc_hull.api.audit_log import api_audit_log
from ycc_hull.api.boats import api_boats
from ycc_hull.api.helpers import api_helpers
from ycc_hull.api.holidays import api_holidays
from ycc_hull.api.licences import api_licences
from ycc_hull.api.members import api_members

# Register all API routers once
app_test.include_router(api_audit_log)
app_test.include_router(api_boats)
app_test.include_router(api_helpers)
app_test.include_router(api_holidays)
app_test.include_router(api_licences)
app_test.include_router(api_members)


# Shared test client
client = TestClient(app_test)


@pytest_asyncio.fixture(scope="module", autouse=True)
async def init_database(request: pytest.FixtureRequest) -> None:
    """Initialise a per-module test database."""
    await init_test_database(request.module.__name__)
