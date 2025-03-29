"""
Helpers API tests.
"""

import json
from datetime import timedelta

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select

from tests.main_test import FakeAuth, app_test, init_test_database
from ycc_hull.api.helpers import api_helpers
from ycc_hull.db.context import DatabaseContextHolder
from ycc_hull.db.entities import AuditLogEntryEntity
from ycc_hull.models.helpers_dtos import HelperTaskDto
from ycc_hull.utils import get_now

app_test.include_router(api_helpers)
client = TestClient(app_test)

future_day = (get_now().date() + timedelta(days=5)).strftime("%Y-%m-%d")
SHORT_DESCRIPTION = " The Club needs your help for this task! \n "
SANITISED_SHORT_DESCRIPTION = "The Club needs your help for this task!"

task_creation_shift = {
    "categoryId": 1,
    "title": " Test Task \n ",
    "shortDescription": SHORT_DESCRIPTION,
    "longDescription": None,
    "contactId": 2,
    "startsAt": f" {future_day}T18:00:00 \n ",
    "endsAt": f" {future_day}T20:30:00 \n ",
    "deadline": None,
    "urgent": False,
    "captainRequiredLicenceInfoId": 9,
    "helperMinCount": 1,
    "helperMaxCount": 2,
    "published": False,
}

task_creation_deadline = {
    "categoryId": 2,
    "title": " Test Task \n ",
    "shortDescription": SHORT_DESCRIPTION,
    "longDescription": " Really! It is very important to get this done! \n ",
    "contactId": 1,
    "urgent": True,
    "starts_at": None,
    "ends_at": None,
    "deadline": f" {future_day}T20:00:00 \n ",
    "captainRequiredLicenceInfoId": None,
    "helperMinCount": 2,
    "helperMaxCount": 2,
    "published": True,
}


task_update_shift = {**task_creation_shift, "notifySignedUpMembers": True}

task_update_deadline = {**task_creation_deadline, "notifySignedUpMembers": False}

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
    with DatabaseContextHolder.context.session() as session:
        entry = session.scalar(
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

    assert audit_data.keys() == {"diff", "old", "new", "notifySignedUpMembers"}
    if old_short_description != new_short_description:
        assert audit_data["diff"]["shortDescription"] == {
            "old": old_short_description,
            "new": new_short_description,
        }

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
    response = client.post("/api/v1/helpers/tasks", json=task_creation_shift)

    # Then
    assert response.status_code == 200
    response_dto = HelperTaskDto(**response.json())
    assert SANITISED_SHORT_DESCRIPTION == response_dto.short_description

    await verify_creation_audit_log_entry(response_dto.short_description)


@pytest.mark.asyncio
async def test_create_task_as_admin() -> None:
    # Given
    FakeAuth.set_helpers_app_admin()

    # When
    response = client.post("/api/v1/helpers/tasks", json=task_creation_deadline)

    # Then
    assert response.status_code == 200
    response_dto = HelperTaskDto(**response.json())
    assert SANITISED_SHORT_DESCRIPTION == response_dto.short_description

    await verify_creation_audit_log_entry(response_dto.short_description)


def test_create_task_fails_if_not_admin_nor_editor() -> None:
    # Given
    FakeAuth.set_member()

    # When
    response = client.post("/api/v1/helpers/tasks", json=task_creation_shift)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You do not have permission to create helper tasks"
    }


def test_create_task_fails_if_editor_but_not_contact() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.post("/api/v1/helpers/tasks", json=task_creation_deadline)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You have to be the contact for the tasks you create"
    }


@pytest.mark.asyncio
async def test_update_task_as_editor() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()
    request = task_creation_shift.copy()
    request["contactId"] = 2
    task_id = client.post("/api/v1/helpers/tasks", json=request).json()["id"]

    # When
    request = task_update_deadline.copy()
    request["contactId"] = 2
    response = client.put(f"/api/v1/helpers/tasks/{task_id}", json=request)

    # Then
    assert response.status_code == 200
    response_dto = HelperTaskDto(**response.json())
    assert task_id == response_dto.id
    assert SANITISED_SHORT_DESCRIPTION == response_dto.short_description

    await verify_update_audit_log_entry(
        task_id,
        SANITISED_SHORT_DESCRIPTION,
        response_dto.short_description,
    )


def test_update_task_fails_if_not_admin_nor_editor() -> None:
    # Given
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v1/helpers/tasks", json=task_creation_shift).json()[
        "id"
    ]
    FakeAuth.set_member()

    # When
    response = client.put(f"/api/v1/helpers/tasks/{task_id}", json=task_update_deadline)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You do not have permission to update helper tasks"
    }


def test_update_task_fails_if_editor_but_not_contact() -> None:
    # Given
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v1/helpers/tasks", json=task_creation_shift).json()[
        "id"
    ]
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.put(f"/api/v1/helpers/tasks/{task_id}", json=task_update_deadline)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You have to be the contact for the tasks you update"
    }


def test_update_task_if_anyone_signed_up() -> None:
    # Given
    request = task_creation_shift.copy()
    request["published"] = True
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v1/helpers/tasks", json=request).json()["id"]

    FakeAuth.set_member()
    assert (
        client.post(f"/api/v1/helpers/tasks/{task_id}/sign-up-as-helper").status_code
        == 200
    )

    FakeAuth.set_helpers_app_admin()

    # When
    request = task_update_shift.copy()
    request["title"] = "Title 2"
    request["shortDescription"] = "Short description 2"
    request["longDescription"] = "Long description 2"
    request["contactId"] = 123
    request["endsAt"] = f" {future_day}T21:00:00 \n "
    request["urgent"] = not request["urgent"]
    request["published"] = True

    response = client.put(f"/api/v1/helpers/tasks/{task_id}", json=request)

    # Then
    assert (
        response.status_code == 200
        and response.json()["shortDescription"] == "Short description 2"
    )


def test_update_task_cannot_unpublish_if_anyone_signed_up() -> None:
    # Given
    request = task_creation_deadline.copy()
    request["published"] = True
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v1/helpers/tasks", json=request).json()["id"]

    FakeAuth.set_member()
    assert (
        client.post(f"/api/v1/helpers/tasks/{task_id}/sign-up-as-captain").status_code
        == 200
    )

    FakeAuth.set_helpers_app_admin()

    # When
    request = task_update_deadline.copy()
    request["published"] = False
    response = client.put(f"/api/v1/helpers/tasks/{task_id}", json=request)

    # Then
    assert response.status_code == 409 and response.json() == {
        "detail": "You must publish a task after anyone has signed up"
    }
