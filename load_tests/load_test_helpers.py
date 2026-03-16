"""Helpers API load tests."""

import random

from locust import HttpUser, task

from load_tests.load_test_auth_utils import get_access_token, get_user_id
from load_tests.load_test_config import ADMIN_USER, OTHER_USER
from load_tests.load_test_helpers_utils import (
    create_task,
    get_task,
    get_tasks,
    sign_up_as_captain,
    sign_up_as_helper,
)

ADMIN_ACCESS_TOKEN = get_access_token(ADMIN_USER)
ADMIN_ID = get_user_id(ADMIN_ACCESS_TOKEN)
OTHER_ACCESS_TOKEN = get_access_token(OTHER_USER)
OTHER_ID = get_user_id(OTHER_ACCESS_TOKEN)


def get_random_access_token() -> str:
    """Return a random access token for load testing."""
    return random.choice([ADMIN_ACCESS_TOKEN, OTHER_ACCESS_TOKEN])  # noqa: S311


class HelpersLoadTest(HttpUser):
    """Helpers API load test."""

    @task
    def list_tasks(self) -> None:
        """List all tasks."""
        get_tasks(self.client, get_random_access_token())

    @task
    def list_and_get_task(self) -> None:
        """List tasks and get a random one."""
        access_token = get_random_access_token()
        tasks = get_tasks(self.client, access_token)

        get_task(self.client, random.choice(tasks)["id"], access_token)  # noqa: S311

    @task
    def create_and_get_task(self) -> None:
        """Create a task."""
        create_task(self.client, ADMIN_ID, ADMIN_ACCESS_TOKEN)

    @task
    def create_and_get_task_and_sign_up(self) -> None:
        """Create a task and sign up members."""
        task_ = create_task(self.client, ADMIN_ID, ADMIN_ACCESS_TOKEN)
        sign_up_as_captain(self.client, task_["id"], ADMIN_ACCESS_TOKEN)
        sign_up_as_helper(self.client, task_["id"], OTHER_ACCESS_TOKEN)
