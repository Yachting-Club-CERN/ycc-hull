"""
Helpers API tests.
"""
import json

from fastapi.testclient import TestClient

from tests.app_test import FakeAuth, app_test, init_test_database
from ycc_hull.api.helpers import api_helpers
from ycc_hull.db.context import DatabaseContextHolder
from ycc_hull.db.entities import AuditLogEntryEntity
from ycc_hull.models.helpers_dtos import HelperTaskDto

app_test.include_router(api_helpers)
client = TestClient(app_test)

task_creation_shift = {
    "categoryId": 1,
    "title": "Test Task",
    "shortDescription": "The Club needs your help for this shift!",
    "contactId": 1,
    "start": "2023-05-01T18:00:00",
    "end": "2023-05-01T20:30:00",
    "urgent": False,
    "captainRequiredLicenceId": 9,
    "helpersMinCount": 1,
    "helpersMaxCount": 2,
    "published": False,
}

task_creation_deadline = {
    "categoryId": 2,
    "title": "Test Task",
    "shortDescription": "The Club needs your help for this task!",
    "longDescription": "Really! It is very important to get this done!",
    "contactId": 2,
    "urgent": True,
    "deadline": "2023-05-02T20:00:00",
    "helpersMinCount": 2,
    "helpersMaxCount": 2,
    "published": True,
}


init_test_database(__name__)


def get_last_audit_log_entry() -> AuditLogEntryEntity:
    with DatabaseContextHolder.context.create_session() as session:
        result = (
            session.query(AuditLogEntryEntity)
            .order_by(AuditLogEntryEntity.id.desc())
            .first()
        )
        if result is None:
            raise AssertionError("No audit log entry found")

        return result


def verify_creation_audit_log_entry(short_description: str) -> None:
    audit = get_last_audit_log_entry()
    assert audit.application.startswith("YCC Hull")
    assert audit.user == "testuser"
    assert audit.description == "Helpers/Tasks/Create"
    assert audit.data is not None

    audit_data = json.loads(audit.data)
    assert audit_data.keys() == {"new"}
    assert audit_data["new"]["@type"] == "ycc_hull.db.entities.HelperTaskEntity"
    assert audit_data["new"]["short_description"] == short_description
    assert set(audit_data["new"].keys()) == set(
        [
            "@type",
            "category_id",
            "title",
            "short_description",
            "long_description",
            "contact_id",
            "start",
            "end",
            "deadline",
            "urgent",
            "captain_required_licence_info_id",
            "helpers_min_count",
            "helpers_max_count",
            "published",
        ]
    )


def test_create_task_as_editor() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.post("/api/v0/helpers/tasks", json=task_creation_shift)

    # Then
    assert response.status_code == 200
    response_dto = HelperTaskDto(**response.json())
    assert task_creation_shift["shortDescription"] == response_dto.short_description

    verify_creation_audit_log_entry(response_dto.short_description)


def test_create_task_as_admin() -> None:
    # Given
    FakeAuth.set_helpers_app_admin()

    # When
    response = client.post("/api/v0/helpers/tasks", json=task_creation_deadline)

    # Then
    assert response.status_code == 200
    response_dto = HelperTaskDto(**response.json())
    assert task_creation_deadline["shortDescription"] == response_dto.short_description

    verify_creation_audit_log_entry(response_dto.short_description)


def test_create_task_fails_if_not_admin_nor_editor() -> None:
    # Given
    FakeAuth.set_member()

    # When
    response = client.post("/api/v0/helpers/tasks", json=task_creation_shift)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You do not have permission to create helper tasks"
    }


def test_create_task_fails_if_editor_but_not_contact() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.post("/api/v0/helpers/tasks", json=task_creation_deadline)

    # Then
    assert response.status_code == 403 and response.json() == {
        "detail": "You have to be the contact for the tasks you create"
    }


# def test_helper_tasks_create_success():
#     # Arrange
#     task_data = {
#         "title": "Test Task",
#         "description": "Testing FastAPI",
#         "contact_id": 1,
#     }
#     user_data = {"username": "testuser", "helpers_app_admin": True}
#     task = HelperTaskCreationRequestDto(**task_data)
#     user = User(**user_data)

#     # Act
#     response = await client.post(
#         "/api/v0/helpers/tasks", json={"task": task_data}, auth=(user.username, "")
#     )

#     # Assert
#     assert response.status_code == 200
#     assert response.json() == {"id": 1, **task_data}


# def test_helper_tasks_create_unauthorized():
#     # Arrange
#     task_data = {
#         "title": "Test Task",
#         "description": "Testing FastAPI",
#         "contact_id": 1,
#     }
#     user_data = {
#         "username": "testuser",
#         "helpers_app_admin": False,
#         "helpers_app_editor": False,
#     }
#     task = HelperTaskCreationRequestDto(**task_data)
#     user = User(**user_data)
#     client = AsyncClient(app=app, base_url="http://test")

#     # Act
#     response = await client.post(
#         "/api/v0/helpers/tasks", json={"task": task_data}, auth=(user.username, "")
#     )

#     # Assert
#     assert response.status_code == 403
#     assert response.json() == {
#         "detail": "You do not have permission to create helper tasks"
#     }


# def test_helper_tasks_create_editor_wrong_contact():
#     # Arrange
#     task_data = {
#         "title": "Test Task",
#         "description": "Testing FastAPI",
#         "contact_id": 2,
#     }
#     user_data = {"username": "testuser", "member_id": 1, "helpers_app_editor": True}
#     task = HelperTaskCreationRequestDto(**task_data)
#     user = User(**user_data)
#     client = AsyncClient(app=app, base_url="http://test")

#     # Act
#     response = await client.post(
#         "/api/v0/helpers/tasks", json={"task": task_data}, auth=(user.username, "")
#     )

#     # Assert
#     assert response.status_code == 403
#     assert response.json() == {
#         "detail": "You have to be the contact for the tasks you create"
#     }


# @pytest.mark.asyncio
# async def test_helper_tasks_create_missing_input():
#     # Arrange
#     task_data = {"title": "Test Task"}
#     user_data = {"username": "testuser", "helpers_app_admin": True}
#     task = HelperTaskCreationRequestDto(**task_data)
#     user = User(**user_data)
#     client = AsyncClient(app=app, base_url="http://test")

#     # Act
#     response = await client.post(
#         "/api/v0/helpers/tasks", json={"task": task_data}, auth=(user.username, "")
#     )

#     # Assert
#     assert response.status_code == 422
#     assert response.json() == {
#         "detail": [
#             {
#                 "loc": ["body", "description"],
#                 "msg": "field required",
#                 "type": "value_error.missing",
#             }
#         ]
#     }


# # @pytest.mark.asyncio
# # async def test_helper_tasks_create_invalid_input():
# #     # Arrange
# #     task_data = {"title": "Test Task", "description": "Testing FastAPI", "contact_id": "invalid"}
# #     user_data = {"username":
