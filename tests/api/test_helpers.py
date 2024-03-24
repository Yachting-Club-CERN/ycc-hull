"""
Helpers API tests.
"""

import json
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select

from tests.main_test import FakeAuth, app_test, init_test_database
from ycc_hull.api.helpers import api_helpers
from ycc_hull.db.context import DatabaseContextHolder
from ycc_hull.db.entities import AuditLogEntryEntity
from ycc_hull.models.helpers_dtos import HelperTaskDto

app_test.include_router(api_helpers)
client = TestClient(app_test)

future_day = (datetime.now().date() + timedelta(days=5)).strftime("%Y-%m-%d")

task_mutation_shift = {
    "categoryId": 1,
    "title": "Test Task",
    "shortDescription": "The Club needs your help for this shift!",
    "longDescription": None,
    "contactId": 2,
    "startsAt": f"{future_day}T18:00:00",
    "endsAt": f"{future_day}T20:30:00",
    "deadline": None,
    "urgent": False,
    "captainRequiredLicenceInfoId": 9,
    "helperMinCount": 1,
    "helperMaxCount": 2,
    "published": False,
}

task_mutation_deadline = {
    "categoryId": 2,
    "title": "Test Task",
    "shortDescription": "The Club needs your help for this task!",
    "longDescription": "Really! It is very important to get this done!",
    "contactId": 1,
    "urgent": True,
    "starts_at": None,
    "ends_at": None,
    "deadline": f"{future_day}T20:00:00",
    "captainRequiredLicenceInfoId": None,
    "helperMinCount": 2,
    "helperMaxCount": 2,
    "published": True,
}

audit_keys = set(
    [
        "@type",
        "id",
        "category",
        "title",
        "shortDescription",
        "longDescription",
        "contact",
        "startsAt",
        "endsAt",
        "deadline",
        "urgent",
        "captainRequiredLicenceInfo",
        "helperMinCount",
        "helperMaxCount",
        "published",
        "captain",
        "helpers",
        "markedAsDoneAt",
        "markedAsDoneBy",
        "markedAsDoneComment",
        "validatedAt",
        "validatedBy",
        "validationComment",
    ]
)


@pytest_asyncio.fixture(scope="module", autouse=True)
async def init_database() -> None:
    await init_test_database(__name__)


async def get_last_audit_log_entry() -> AuditLogEntryEntity:
    async with DatabaseContextHolder.context.async_session() as session:
        entry = await session.scalar(
            select(AuditLogEntryEntity).order_by(AuditLogEntryEntity.id.desc()).limit(1)
        )
        if not entry:
            raise AssertionError("No audit log entry found")
        return entry


async def verify_creation_audit_log_entry(short_description: str) -> None:
    audit = await get_last_audit_log_entry()
    assert audit.application.startswith("YCC Hull")
    assert audit.principal == "testuser"
    assert audit.description == "Helpers/Tasks/Create"
    assert audit.data is not None

    audit_data = json.loads(audit.data)

    assert audit_data.keys() == {"new"}

    assert audit_data["new"]["@type"] == "ycc_hull.models.helpers_dtos.HelperTaskDto"
    assert audit_data["new"]["shortDescription"] == short_description
    assert audit_data["new"].keys() == audit_keys


async def verify_update_audit_log_entry(
    task_id: int, old_short_description: str, new_short_description: str
) -> None:
    audit = await get_last_audit_log_entry()
    assert audit.application.startswith("YCC Hull")
    assert audit.principal == "testuser"
    assert audit.description == f"Helpers/Tasks/Update/{task_id}"
    assert audit.data is not None

    audit_data = json.loads(audit.data)

    assert audit_data.keys() == {"old", "new"}

    assert audit_data["old"]["@type"] == "ycc_hull.models.helpers_dtos.HelperTaskDto"
    assert audit_data["old"]["id"] == task_id
    assert audit_data["old"]["shortDescription"] == old_short_description
    assert audit_data["old"].keys() == audit_keys

    assert audit_data["new"]["@type"] == "ycc_hull.models.helpers_dtos.HelperTaskDto"
    assert audit_data["new"]["id"] == task_id
    assert audit_data["new"]["shortDescription"] == new_short_description
    assert audit_data["new"].keys() == audit_keys


@pytest.mark.asyncio
async def test_create_task_as_editor() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.post("/api/v1/helpers/tasks", json=task_mutation_shift)

    # Then
    assert response.status_code == 200
    response_dto = HelperTaskDto(**response.json())
    assert task_mutation_shift["shortDescription"] == response_dto.short_description

    await verify_creation_audit_log_entry(response_dto.short_description)


@pytest.mark.asyncio
async def test_create_task_as_admin() -> None:
    # Given
    FakeAuth.set_helpers_app_admin()

    # When
    response = client.post("/api/v1/helpers/tasks", json=task_mutation_deadline)

    # Then
    assert response.status_code == 200
    response_dto = HelperTaskDto(**response.json())
    assert task_mutation_deadline["shortDescription"] == response_dto.short_description

    await verify_creation_audit_log_entry(response_dto.short_description)


def test_create_task_fails_if_not_admin_nor_editor() -> None:
    # Given
    FakeAuth.set_member()

    # When
    response = client.post("/api/v1/helpers/tasks", json=task_mutation_shift)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You do not have permission to create helper tasks"
    }


def test_create_task_fails_if_editor_but_not_contact() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.post("/api/v1/helpers/tasks", json=task_mutation_deadline)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You have to be the contact for the tasks you create"
    }


@pytest.mark.asyncio
async def test_update_task_as_editor() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()
    task_mutation = task_mutation_shift.copy()
    task_mutation["contactId"] = 2
    task_id = client.post("/api/v1/helpers/tasks", json=task_mutation).json()["id"]

    # When
    task_mutation = task_mutation_deadline.copy()
    task_mutation["contactId"] = 2
    response = client.put(f"/api/v1/helpers/tasks/{task_id}", json=task_mutation)

    # Then
    assert response.status_code == 200
    response_dto = HelperTaskDto(**response.json())
    assert task_id == response_dto.id
    assert task_mutation_deadline["shortDescription"] == response_dto.short_description

    await verify_update_audit_log_entry(
        task_id,
        str(task_mutation_shift["shortDescription"]),
        response_dto.short_description,
    )


def test_update_task_fails_if_not_admin_nor_editor() -> None:
    # Given
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v1/helpers/tasks", json=task_mutation_shift).json()[
        "id"
    ]
    FakeAuth.set_member()

    # When
    response = client.put(
        f"/api/v1/helpers/tasks/{task_id}", json=task_mutation_deadline
    )

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You do not have permission to update helper tasks"
    }


def test_update_task_fails_if_editor_but_not_contact() -> None:
    # Given
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v1/helpers/tasks", json=task_mutation_deadline).json()[
        "id"
    ]
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.put(f"/api/v1/helpers/tasks/{task_id}", json=task_mutation_shift)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You have to be the contact for the tasks you update"
    }


def test_update_task_if_anyone_signed_up() -> None:
    # Given
    task_mutation = task_mutation_shift.copy()
    task_mutation["published"] = True
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v1/helpers/tasks", json=task_mutation).json()["id"]

    FakeAuth.set_member()
    assert (
        client.post(f"/api/v1/helpers/tasks/{task_id}/sign-up-as-helper").status_code
        == 200
    )

    FakeAuth.set_helpers_app_admin()

    # When
    task_mutation["title"] = "Title 2"
    task_mutation["shortDescription"] = "Short description 2"
    task_mutation["longDescription"] = "Long description 2"
    task_mutation["contactId"] = 123
    task_mutation["urgent"] = not task_mutation["urgent"]

    response = client.put(f"/api/v1/helpers/tasks/{task_id}", json=task_mutation)

    # Then
    assert (
        response.status_code == 200
        and response.json()["shortDescription"] == "Short description 2"
    )


def test_update_task_cannot_change_timing_if_anyone_signed_up() -> None:
    # Given
    task_mutation = task_mutation_shift.copy()
    task_mutation["published"] = True
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v1/helpers/tasks", json=task_mutation).json()["id"]

    FakeAuth.set_member()
    assert (
        client.post(f"/api/v1/helpers/tasks/{task_id}/sign-up-as-helper").status_code
        == 200
    )

    FakeAuth.set_helpers_app_admin()

    # When
    task_mutation["endsAt"] = f"{future_day}T21:00:00"
    response = client.put(f"/api/v1/helpers/tasks/{task_id}", json=task_mutation)

    # Then
    assert response.status_code == 409 and response.json() == {
        "detail": "Cannot change timing after anyone has signed up"
    }


def test_update_task_cannot_unpublish_if_anyone_signed_up() -> None:
    # Given
    task_mutation = task_mutation_deadline.copy()
    task_mutation["published"] = True
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v1/helpers/tasks", json=task_mutation).json()["id"]

    FakeAuth.set_member()
    assert (
        client.post(f"/api/v1/helpers/tasks/{task_id}/sign-up-as-captain").status_code
        == 200
    )

    FakeAuth.set_helpers_app_admin()

    # When
    task_mutation["published"] = False
    response = client.put(f"/api/v1/helpers/tasks/{task_id}", json=task_mutation)

    # Then
    assert response.status_code == 409 and response.json() == {
        "detail": "You must publish a task after anyone has signed up"
    }
