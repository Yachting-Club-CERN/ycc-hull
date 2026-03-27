"""Helpers API tests."""

from datetime import timedelta

import pytest

from tests.api.conftest import client
from tests.api.helpers_test_utils import (
    ANY,
    CATEGORY_MAINTENANCE,
    CATEGORY_RESPONSE_KEYS,
    CATEGORY_SURVEILLANCE,
    MEMBER_1,
    MEMBER_2,
    TASK_RESPONSE_KEYS,
    assert_task_json,
    create_deadline_task,
    create_shift_task,
    future_day,
    helper_entry,
    past_day,
    sign_up_captain,
    sign_up_helper,
    update_request_from,
    verify_creation_audit_log_entry,
    verify_update_audit_log_entry,
)
from tests.main_test import FakeAuth
from ycc_hull.utils import get_now

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
    "startsAt": None,
    "endsAt": None,
    "deadline": f" {future_day}T20:00:00 \n ",
    "captainRequiredLicenceInfoId": None,
    "helperMinCount": 2,
    "helperMaxCount": 2,
    "published": True,
}


task_update_shift = {**task_creation_shift, "notifySignedUpMembers": True}

task_update_deadline = {**task_creation_deadline, "notifySignedUpMembers": False}


# ==============================================================================
# Create Task
# ==============================================================================


@pytest.mark.asyncio
async def test_create_task_as_editor() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.post("/api/v1/helpers/tasks", json=task_creation_shift)

    # Then
    assert response.status_code == 200
    data = response.json()
    assert_task_json(
        data,
        category=CATEGORY_SURVEILLANCE,
        title="Test Task",
        short_description=SANITISED_SHORT_DESCRIPTION,
        long_description=None,
        contact=MEMBER_2,
        starts_at=f"{future_day}T18:00:00",
        ends_at=f"{future_day}T20:30:00",
        deadline=None,
        urgent=False,
        captain_required_licence_info={"id": 9, "licence": "M"},
        helper_min_count=1,
        helper_max_count=2,
        published=False,
        captain=None,
        helpers=[],
    )

    verify_creation_audit_log_entry(data["shortDescription"])


@pytest.mark.asyncio
async def test_create_task_as_admin() -> None:
    # Given
    FakeAuth.set_helpers_app_admin()

    # When
    response = client.post("/api/v1/helpers/tasks", json=task_creation_deadline)

    # Then
    assert response.status_code == 200
    data = response.json()
    assert_task_json(
        data,
        category=CATEGORY_MAINTENANCE,
        title="Test Task",
        short_description=SANITISED_SHORT_DESCRIPTION,
        long_description="<p>Really! It is very important to get this done!</p>",
        contact=MEMBER_1,
        starts_at=None,
        ends_at=None,
        deadline=f"{future_day}T20:00:00",
        urgent=True,
        captain_required_licence_info=None,
        helper_min_count=2,
        helper_max_count=2,
        published=True,
        captain=None,
        helpers=[],
    )

    verify_creation_audit_log_entry(data["shortDescription"])


def test_create_task_fails_if_not_admin_nor_editor() -> None:
    # Given
    FakeAuth.set_member()

    # When
    response = client.post("/api/v1/helpers/tasks", json=task_creation_shift)

    # Then
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to create helper tasks"
    }


def test_create_task_fails_if_editor_but_not_contact() -> None:
    # Given
    FakeAuth.set_helpers_app_editor()

    # When
    response = client.post("/api/v1/helpers/tasks", json=task_creation_deadline)

    # Then
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You have to be the contact for the tasks you create"
    }


# ==============================================================================
# Update Task (existing tests)
# ==============================================================================


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
    data = response.json()
    assert_task_json(
        data,
        category=CATEGORY_MAINTENANCE,
        title="Test Task",
        short_description=SANITISED_SHORT_DESCRIPTION,
        long_description="<p>Really! It is very important to get this done!</p>",
        contact=MEMBER_2,
        starts_at=None,
        ends_at=None,
        deadline=f"{future_day}T20:00:00",
        urgent=True,
        captain_required_licence_info=None,
        helper_min_count=2,
        helper_max_count=2,
        published=True,
        captain=None,
        helpers=[],
    )

    verify_update_audit_log_entry(
        task_id,
        SANITISED_SHORT_DESCRIPTION,
        data["shortDescription"],
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
    assert response.status_code == 403
    assert response.json() == {
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
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You have to be the contact for the tasks you update"
    }


def test_update_task_if_anyone_signed_up() -> None:
    # Given
    request = task_creation_shift.copy()
    request["published"] = True
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v1/helpers/tasks", json=request).json()["id"]

    sign_up_helper(client, task_id)

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
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Title 2"
    assert data["shortDescription"] == "Short description 2"
    assert data["longDescription"] == "<p>Long description 2</p>"
    assert data["contact"]["id"] == 123
    assert data["endsAt"].startswith(f"{future_day}T21:00:00")
    assert data["urgent"] is not task_creation_shift["urgent"]
    assert data["published"] is True
    assert len(data["helpers"]) == 1
    assert data["helpers"][0]["member"]["id"] == 100


def test_update_task_cannot_unpublish_if_anyone_signed_up() -> None:
    # Given
    request = task_creation_deadline.copy()
    request["published"] = True
    FakeAuth.set_helpers_app_admin()
    task_id = client.post("/api/v1/helpers/tasks", json=request).json()["id"]

    sign_up_captain(client, task_id)

    FakeAuth.set_helpers_app_admin()

    # When
    request = task_update_deadline.copy()
    request["published"] = False
    response = client.put(f"/api/v1/helpers/tasks/{task_id}", json=request)

    # Then
    assert response.status_code == 409
    assert response.json() == {
        "detail": "You must publish a task after anyone has signed up"
    }


# ==============================================================================
# Find All Task Categories
# ==============================================================================


def test_find_all_task_categories() -> None:
    FakeAuth.set_member()

    response = client.get("/api/v1/helpers/task-categories")

    assert response.status_code == 200
    categories = response.json()
    assert len(categories) == 2
    for cat in categories:
        assert cat.keys() == CATEGORY_RESPONSE_KEYS
    assert categories[0]["title"] == "Maintenance / General"
    assert categories[0]["shortDescription"] == "General maintenance"
    assert categories[1]["title"] == "Surveillance"
    assert categories[1]["shortDescription"] == "Q-boat surveillance"


# ==============================================================================
# Find All Tasks
# ==============================================================================


def test_find_all_tasks_as_member() -> None:
    FakeAuth.set_member()

    response = client.get("/api/v1/helpers/tasks", params={"year": get_now().year})

    assert response.status_code == 200
    tasks = response.json()
    assert all(t["published"] for t in tasks)
    task_ids = {t["id"] for t in tasks}
    assert {2011, 2012, 2021, 2022, 2031, 2032, 2033} <= task_ids
    assert 2023 not in task_ids
    for t in tasks:
        assert t.keys() == TASK_RESPONSE_KEYS


def test_find_all_tasks_as_admin_includes_unpublished() -> None:
    FakeAuth.set_helpers_app_admin()

    response = client.get("/api/v1/helpers/tasks", params={"year": get_now().year})

    assert response.status_code == 200
    tasks = response.json()
    published_values = {t["published"] for t in tasks}
    assert published_values == {True, False}


def test_find_all_tasks_member_cannot_access_other_years() -> None:
    FakeAuth.set_member()

    response = client.get("/api/v1/helpers/tasks", params={"year": get_now().year - 1})

    assert response.status_code == 403
    assert response.json() == {
        "detail": f"You do not have permission to list tasks for {get_now().year - 1}"
    }


# ==============================================================================
# Find Task By ID
# ==============================================================================


def test_find_task_by_id() -> None:
    FakeAuth.set_helpers_app_admin()

    response = client.get("/api/v1/helpers/tasks/2021")

    assert response.status_code == 200
    task = response.json()
    assert task.keys() == TASK_RESPONSE_KEYS
    assert task["id"] == 2021
    assert task["title"] == "Surveillance"
    assert task["shortDescription"] == "Fictional December D/Y practice"
    assert task["category"]["title"] == "Surveillance"
    assert task["contact"]["id"] == 1
    assert task["published"] is True
    assert task["captain"] is None
    assert task["helpers"] == []
    assert task["markedAsDoneAt"] is None
    assert task["validatedAt"] is None


def test_find_task_by_id_not_found() -> None:
    FakeAuth.set_helpers_app_admin()

    response = client.get("/api/v1/helpers/tasks/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


# ==============================================================================
# Update Task - _check_can_update_task coverage
# ==============================================================================


def test_update_task_cannot_change_year_if_anyone_signed_up() -> None:
    task = create_shift_task(client, published=True)
    sign_up_helper(client, task["id"])
    FakeAuth.set_helpers_app_admin()

    next_year_day = (get_now().date() + timedelta(days=400)).strftime("%Y-%m-%d")
    update = update_request_from(
        task,
        startsAt=f"{next_year_day}T10:00:00",
        endsAt=f"{next_year_day}T18:00:00",
        published=True,
    )
    response = client.put(f"/api/v1/helpers/tasks/{task['id']}", json=update)

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "You cannot change the year of the task after anyone has"
            " signed up. Please create a new task instead."
        )
    }


def test_update_task_cannot_reduce_helper_max_below_signed_up() -> None:
    task = create_shift_task(client, published=True, helper_max_count=3)
    sign_up_helper(client, task["id"], member_id=100)
    sign_up_helper(client, task["id"], member_id=101)
    FakeAuth.set_helpers_app_admin()

    update = update_request_from(task, helperMaxCount=1, published=True)
    response = client.put(f"/api/v1/helpers/tasks/{task['id']}", json=update)

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Cannot set the maximum number of helpers below the"
            " number of already signed up helpers (2)"
        )
    }


def test_update_task_cannot_change_captain_licence_if_captain_lacks_it() -> None:
    task = create_deadline_task(client, published=True)
    sign_up_captain(client, task["id"], member_id=100)
    FakeAuth.set_helpers_app_admin()

    task = client.get(f"/api/v1/helpers/tasks/{task['id']}").json()

    update = update_request_from(task, captainRequiredLicenceInfoId=9, published=True)
    response = client.put(f"/api/v1/helpers/tasks/{task['id']}", json=update)

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Cannot change captain required licence info because"
            " the signed up captain does not have the newly"
            " specified licence"
        )
    }


def test_update_task_can_change_captain_licence_if_captain_has_it() -> None:
    task = create_deadline_task(client, published=True)
    sign_up_captain(client, task["id"], member_id=4)  # member 4 has licence 9
    FakeAuth.set_helpers_app_admin()
    task = client.get(f"/api/v1/helpers/tasks/{task['id']}").json()

    update = update_request_from(
        task,
        captainRequiredLicenceInfoId=9,
        published=True,
    )
    response = client.put(f"/api/v1/helpers/tasks/{task['id']}", json=update)

    assert response.status_code == 200
    assert_task_json(
        response.json(),
        category=CATEGORY_MAINTENANCE,
        title="Test Task",
        short_description="Test task description",
        long_description=None,
        contact=MEMBER_1,
        starts_at=None,
        ends_at=None,
        deadline=f"{future_day}T20:00:00",
        urgent=False,
        captain_required_licence_info={"id": 9, "licence": "M"},
        helper_min_count=1,
        helper_max_count=2,
        published=True,
        captain=helper_entry(4),
        helpers=[],
    )


def test_update_task_clears_urgent_when_validated() -> None:
    task = create_deadline_task(
        client,
        published=True,
        deadline=f"{past_day}T20:00:00",
        urgent=True,
    )
    FakeAuth.set_helpers_app_admin()
    client.post(
        f"/api/v1/helpers/tasks/{task['id']}/mark-as-done",
        json={"comment": None},
    )
    client.post(
        f"/api/v1/helpers/tasks/{task['id']}/validate",
        json={"comment": None},
    )

    task = client.get(f"/api/v1/helpers/tasks/{task['id']}").json()

    update = update_request_from(task, urgent=True, published=True)
    response = client.put(f"/api/v1/helpers/tasks/{task['id']}", json=update)

    assert response.status_code == 200
    assert_task_json(
        response.json(),
        category=CATEGORY_MAINTENANCE,
        title="Test Task",
        short_description="Test task description",
        long_description=None,
        contact=MEMBER_1,
        starts_at=None,
        ends_at=None,
        deadline=f"{past_day}T20:00:00",
        urgent=False,
        captain_required_licence_info=None,
        helper_min_count=1,
        helper_max_count=2,
        published=True,
        captain=None,
        helpers=[],
        marked_as_done_at=ANY,
        marked_as_done_by=MEMBER_1,
        validated_at=ANY,
        validated_by=MEMBER_1,
    )


def test_update_task_with_notify_signed_up_members() -> None:
    task = create_shift_task(client, published=True)
    sign_up_helper(client, task["id"])
    FakeAuth.set_helpers_app_admin()

    update = update_request_from(
        task,
        shortDescription="Updated description",
        notifySignedUpMembers=True,
        published=True,
    )
    response = client.put(f"/api/v1/helpers/tasks/{task['id']}", json=update)

    assert response.status_code == 200
    assert_task_json(
        response.json(),
        category=CATEGORY_MAINTENANCE,
        title="Test Task",
        short_description="Updated description",
        long_description=None,
        contact=MEMBER_1,
        starts_at=f"{future_day}T10:00:00",
        ends_at=f"{future_day}T18:00:00",
        deadline=None,
        urgent=False,
        captain_required_licence_info=None,
        helper_min_count=1,
        helper_max_count=2,
        published=True,
        captain=None,
        helpers=[helper_entry(100)],
    )
