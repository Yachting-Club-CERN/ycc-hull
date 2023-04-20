"""
Helpers API tests.
"""
import json

from fastapi.testclient import TestClient

from tests.main_test import FakeAuth, app_test, init_test_database
from ycc_hull.api.helpers import api_helpers
from ycc_hull.db.context import DatabaseContextHolder
from ycc_hull.db.entities import AuditLogEntryEntity
from ycc_hull.models.helpers_dtos import HelperTaskDto

app_test.include_router(api_helpers)
client = TestClient(app_test)

task_mutation_shift = {
    "categoryId": 1,
    "title": "Test Task",
    "shortDescription": "The Club needs your help for this shift!",
    "contactId": 2,
    "start": "2023-05-01T18:00:00",
    "end": "2023-05-01T20:30:00",
    "urgent": False,
    "captainRequiredLicenceInfoId": 9,
    "helpersMinCount": 1,
    "helpersMaxCount": 2,
    "published": False,
}

task_mutation_deadline = {
    "categoryId": 2,
    "title": "Test Task",
    "shortDescription": "The Club needs your help for this task!",
    "longDescription": "Really! It is very important to get this done!",
    "contactId": 1,
    "urgent": True,
    "deadline": "2023-05-02T20:00:00",
    "helpersMinCount": 2,
    "helpersMaxCount": 2,
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
        "start",
        "end",
        "deadline",
        "urgent",
        "captainRequiredLicenceInfo",
        "helpersMinCount",
        "helpersMaxCount",
        "published",
        "captain",
        "helpers",
    ]
)

init_test_database(__name__)


def get_last_audit_log_entry() -> AuditLogEntryEntity:
    with DatabaseContextHolder.context.create_session() as session:
        result = (
            session.query(AuditLogEntryEntity)
            .order_by(AuditLogEntryEntity.id.desc())
            .limit(1)
            .one()
        )

        return result


def verify_creation_audit_log_entry(short_description: str) -> None:
    audit = get_last_audit_log_entry()
    assert audit.application.startswith("YCC Hull")
    assert audit.user == "testuser"
    assert audit.description == "Helpers/Tasks/Create"
    assert audit.data is not None

    audit_data = json.loads(audit.data)

    assert audit_data.keys() == {"new"}

    assert audit_data["new"]["@type"] == "ycc_hull.models.helpers_dtos.HelperTaskDto"
    assert audit_data["new"]["shortDescription"] == short_description
    assert audit_data["new"].keys() == audit_keys


def verify_update_audit_log_entry(
    task_id: int, old_short_description: str, new_short_description: str
) -> None:
    audit = get_last_audit_log_entry()
    assert audit.application.startswith("YCC Hull")
    assert audit.user == "testuser"
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


def test_create_task_as_editor() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.post("/api/v0/helpers/tasks", json=task_mutation_shift)

    # Then
    assert response.status_code == 200
    response_dto = HelperTaskDto(**response.json())
    assert task_mutation_shift["shortDescription"] == response_dto.short_description

    verify_creation_audit_log_entry(response_dto.short_description)


def test_create_task_as_admin() -> None:
    # Given
    FakeAuth.set_helpers_app_admin()

    # When
    response = client.post("/api/v0/helpers/tasks", json=task_mutation_deadline)

    # Then
    assert response.status_code == 200
    response_dto = HelperTaskDto(**response.json())
    assert task_mutation_deadline["shortDescription"] == response_dto.short_description

    verify_creation_audit_log_entry(response_dto.short_description)


def test_create_task_fails_if_not_admin_nor_editor() -> None:
    # Given
    FakeAuth.set_member()

    # When
    response = client.post("/api/v0/helpers/tasks", json=task_mutation_shift)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You do not have permission to create helper tasks"
    }


def test_create_task_fails_if_editor_but_not_contact() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.post("/api/v0/helpers/tasks", json=task_mutation_deadline)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You have to be the contact for the tasks you create"
    }


def test_update_task_as_editor() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()
    task_mutation = task_mutation_shift.copy()
    task_mutation["contactId"] = 2
    task_id = client.post("/api/v0/helpers/tasks", json=task_mutation).json()["id"]

    # When
    task_mutation = task_mutation_deadline.copy()
    task_mutation["contactId"] = 2
    response = client.put(f"/api/v0/helpers/tasks/{task_id}", json=task_mutation)

    # Then
    assert response.status_code == 200
    response_dto = HelperTaskDto(**response.json())
    assert task_id == response_dto.id
    assert task_mutation_deadline["shortDescription"] == response_dto.short_description

    verify_update_audit_log_entry(
        task_id,
        str(task_mutation_shift["shortDescription"]),
        response_dto.short_description,
    )


def test_update_task_fails_if_not_admin_nor_editor() -> None:
    # Given
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v0/helpers/tasks", json=task_mutation_shift).json()[
        "id"
    ]
    FakeAuth.set_member()

    # When
    response = client.put(
        f"/api/v0/helpers/tasks/{task_id}", json=task_mutation_deadline
    )

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You do not have permission to update helper tasks"
    }


def test_update_task_fails_if_editor_but_not_contact() -> None:
    # Given
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v0/helpers/tasks", json=task_mutation_deadline).json()[
        "id"
    ]
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.put(f"/api/v0/helpers/tasks/{task_id}", json=task_mutation_shift)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You have to be the contact for the tasks you update"
    }


def test_update_task_if_anyone_subscribed() -> None:
    # Given
    task_mutation = task_mutation_shift.copy()
    task_mutation["published"] = True
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v0/helpers/tasks", json=task_mutation).json()["id"]

    FakeAuth.set_member()
    assert (
        client.post(f"/api/v0/helpers/tasks/{task_id}/subscribe-as-helper").status_code
        == 200
    )

    FakeAuth.set_helpers_app_admin()

    # When
    task_mutation["title"] = "Title 2"
    task_mutation["shortDescription"] = "Short description 2"
    task_mutation["longDescription"] = "Long description 2"
    task_mutation["contactId"] = 123
    task_mutation["urgent"] = not task_mutation["urgent"]

    response = client.put(f"/api/v0/helpers/tasks/{task_id}", json=task_mutation)

    # Then
    assert (
        response.status_code == 200
        and response.json()["shortDescription"] == "Short description 2"
    )


def test_update_task_cannot_change_timing_if_anyone_subscribed() -> None:
    # Given
    task_mutation = task_mutation_shift.copy()
    task_mutation["published"] = True
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v0/helpers/tasks", json=task_mutation).json()["id"]

    FakeAuth.set_member()
    assert (
        client.post(f"/api/v0/helpers/tasks/{task_id}/subscribe-as-helper").status_code
        == 200
    )

    FakeAuth.set_helpers_app_admin()

    # When
    task_mutation["end"] = "2023-05-01T21:00:00"
    response = client.put(f"/api/v0/helpers/tasks/{task_id}", json=task_mutation)

    # Then
    assert response.status_code == 409 and response.json() == {
        "detail": "Cannot change timing after anyone has subscribed"
    }


def test_update_task_cannot_unpublish_if_anyone_subscribed() -> None:
    # Given
    task_mutation = task_mutation_deadline.copy()
    task_mutation["published"] = True
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v0/helpers/tasks", json=task_mutation).json()["id"]

    FakeAuth.set_member()
    assert (
        client.post(f"/api/v0/helpers/tasks/{task_id}/subscribe-as-captain").status_code
        == 200
    )

    FakeAuth.set_helpers_app_admin()

    # When
    task_mutation["published"] = False
    response = client.put(f"/api/v0/helpers/tasks/{task_id}", json=task_mutation)

    # Then
    assert response.status_code == 409 and response.json() == {
        "detail": "You must publish a task after anyone has subscribed"
    }
