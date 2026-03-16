"""Helpers API utilities for load tests."""

import random
from datetime import datetime, timedelta

from locust.clients import HttpSession

from load_tests.load_test_auth_utils import create_auth_header
from load_tests.load_test_config import API_BASE_URL
from ycc_hull.utils import TIME_ZONE


def get_task_categories(client: HttpSession, access_token: str) -> list[dict]:
    """Fetch all task categories."""
    response = client.get(
        f"{API_BASE_URL}/helpers/task-categories",
        headers=create_auth_header(access_token),
    )
    assert response.status_code == 200, response

    task_categories = response.json()
    assert len(task_categories) > 0

    return task_categories


def get_tasks(client: HttpSession, access_token: str) -> list[dict]:
    """Fetch all helper tasks."""
    response = client.get(
        f"{API_BASE_URL}/helpers/tasks",
        params={"year": datetime.now(tz=TIME_ZONE).year},
        headers=create_auth_header(access_token),
    )
    assert response.status_code == 200, response

    tasks = response.json()
    assert len(tasks) > 0

    return tasks


def get_task(client: HttpSession, task_id: int, access_token: str) -> dict:
    """Fetch a single helper task by ID."""
    response = client.get(
        f"{API_BASE_URL}/helpers/tasks/{task_id}",
        headers=create_auth_header(access_token),
    )
    assert response.status_code == 200, response

    task = response.json()
    assert task["id"] == task_id, task

    return task


def create_task(client: HttpSession, contact_id: int, access_token: str) -> dict:
    """Create a helper task via the API."""
    category_id = random.choice(  # noqa: S311
        get_task_categories(client, access_token)
    )["id"]
    now = datetime.now(tz=TIME_ZONE)
    deadline = now + timedelta(hours=random.randint(24, 24 * 10))  # noqa: S311

    response = client.post(
        f"{API_BASE_URL}/helpers/tasks",
        headers=create_auth_header(access_token),
        json={
            "categoryId": category_id,
            "title": f"Load test task @ {now.strftime('%Y-%m-%d %H:%M:%S')}",
            "shortDescription": "Load test task",
            "longDescription": "Load test task",
            "contactId": contact_id,
            "startsAt": None,
            "endsAt": None,
            "deadline": deadline.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "urgent": False,
            "captainRequiredLicenceInfoId": None,
            "helperMinCount": 1,
            "helperMaxCount": 3,
            "published": True,
        },
    )
    assert response.status_code == 200, response

    task = response.json()
    assert task["category"]["id"] == category_id, task
    assert task["contact"]["id"] == contact_id, task

    return task


def sign_up_as_captain(client: HttpSession, task_id: int, access_token: str) -> dict:
    """Sign up as captain for a task."""
    response = client.post(
        f"{API_BASE_URL}/helpers/tasks/{task_id}/sign-up-as-captain",
        headers=create_auth_header(access_token),
    )
    assert response.status_code == 200, response

    task = response.json()
    assert task["id"] == task_id, task
    assert task["captain"]["member"]["id"] is not None, task

    return task


def sign_up_as_helper(client: HttpSession, task_id: int, access_token: str) -> dict:
    """Sign up as helper for a task."""
    response = client.post(
        f"{API_BASE_URL}/helpers/tasks/{task_id}/sign-up-as-helper",
        headers=create_auth_header(access_token),
    )
    assert response.status_code == 200, response

    task = response.json()
    assert task["id"] == task_id, task
    assert len(task["helpers"]) > 0, task

    return task
