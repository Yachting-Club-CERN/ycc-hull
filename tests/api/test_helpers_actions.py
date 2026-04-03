from tests.api.conftest import client
from tests.api.helpers_test_utils import (
    ANY,
    CATEGORY_MAINTENANCE,
    MEMBER_1,
    MEMBER_2,
    assert_task_json,
    create_deadline_task,
    create_shift_task,
    future_day,
    helper_entry,
    past_day,
    sign_up_captain,
    sign_up_helper,
)
from tests.main_test import FakeAuth

# ==============================================================================
# Set Captain / Remove Captain
# ==============================================================================


def test_set_captain_as_admin() -> None:
    task = create_deadline_task(client, published=True)
    FakeAuth.set_helpers_app_admin()

    response = client.put(f"/api/v1/helpers/tasks/{task['id']}/captain/100")

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
        captain_required_licence_info=None,
        helper_min_count=1,
        helper_max_count=2,
        published=True,
        captain=helper_entry(100),
        helpers=[],
    )


def test_set_captain_fails_if_already_has_captain() -> None:
    task = create_deadline_task(client, published=True)
    FakeAuth.set_helpers_app_admin()

    first_resp = client.put(f"/api/v1/helpers/tasks/{task['id']}/captain/100")
    assert first_resp.status_code == 200
    assert first_resp.json()["captain"]["member"]["id"] == 100

    response = client.put(f"/api/v1/helpers/tasks/{task['id']}/captain/101")

    assert response.status_code == 409
    assert response.json() == {"detail": "Task already has a captain"}


def test_set_captain_fails_without_required_licence() -> None:
    task = create_shift_task(
        client,
        published=True,
        captain_required_licence_info_id=9,
    )
    FakeAuth.set_helpers_app_admin()

    response = client.put(f"/api/v1/helpers/tasks/{task['id']}/captain/100")

    assert response.status_code == 409
    assert response.json() == {"detail": "Task captain needs licence: M"}


def test_set_captain_fails_if_already_signed_up_as_helper() -> None:
    task = create_deadline_task(client, published=True)
    sign_up_helper(client, task["id"], member_id=100)
    FakeAuth.set_helpers_app_admin()

    response = client.put(f"/api/v1/helpers/tasks/{task['id']}/captain/100")

    assert response.status_code == 409
    assert response.json() == {"detail": "Already signed up as helper"}


def test_set_captain_fails_if_not_editor_or_admin() -> None:
    task = create_deadline_task(client, published=True)
    FakeAuth.set_member()

    response = client.put(f"/api/v1/helpers/tasks/{task['id']}/captain/100")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to update helper tasks"
    }


def test_remove_captain() -> None:
    task = create_deadline_task(client, published=True)
    sign_up_captain(client, task["id"], member_id=100)
    FakeAuth.set_helpers_app_admin()

    response = client.delete(f"/api/v1/helpers/tasks/{task['id']}/captain")

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
        captain_required_licence_info=None,
        helper_min_count=1,
        helper_max_count=2,
        published=True,
        captain=None,
        helpers=[],
    )


def test_remove_captain_fails_if_no_captain() -> None:
    task = create_deadline_task(client, published=True)
    FakeAuth.set_helpers_app_admin()

    response = client.delete(f"/api/v1/helpers/tasks/{task['id']}/captain")

    assert response.status_code == 409
    assert response.json() == {"detail": "Task has no captain"}


def test_remove_captain_fails_if_not_editor_or_admin() -> None:
    task = create_deadline_task(client, published=True)
    FakeAuth.set_member()

    response = client.delete(f"/api/v1/helpers/tasks/{task['id']}/captain")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to update helper tasks"
    }


# ==============================================================================
# Add Helper / Remove Helper
# ==============================================================================


def test_add_helper_as_admin() -> None:
    task = create_deadline_task(client, published=True)
    FakeAuth.set_helpers_app_admin()

    response = client.put(f"/api/v1/helpers/tasks/{task['id']}/helpers/100")

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
        captain_required_licence_info=None,
        helper_min_count=1,
        helper_max_count=2,
        published=True,
        captain=None,
        helpers=[helper_entry(100)],
    )


def test_add_helper_fails_if_limit_reached() -> None:
    task = create_deadline_task(client, published=True, helper_max_count=1)
    FakeAuth.set_helpers_app_admin()

    first_resp = client.put(f"/api/v1/helpers/tasks/{task['id']}/helpers/100")
    assert first_resp.status_code == 200
    assert first_resp.json()["helpers"][0]["member"]["id"] == 100

    response = client.put(f"/api/v1/helpers/tasks/{task['id']}/helpers/101")

    assert response.status_code == 409
    assert response.json() == {"detail": "Task helper limit reached"}


def test_add_helper_fails_if_already_signed_up_as_captain() -> None:
    task = create_deadline_task(client, published=True)
    sign_up_captain(client, task["id"], member_id=100)
    FakeAuth.set_helpers_app_admin()

    response = client.put(f"/api/v1/helpers/tasks/{task['id']}/helpers/100")

    assert response.status_code == 409
    assert response.json() == {"detail": "Already signed up as captain"}


def test_add_helper_fails_if_already_signed_up_as_helper() -> None:
    task = create_deadline_task(client, published=True)
    sign_up_helper(client, task["id"], member_id=100)
    FakeAuth.set_helpers_app_admin()

    response = client.put(f"/api/v1/helpers/tasks/{task['id']}/helpers/100")

    assert response.status_code == 409
    assert response.json() == {"detail": "Already signed up as helper"}


def test_add_helper_fails_if_not_editor_or_admin() -> None:
    task = create_deadline_task(client, published=True)
    FakeAuth.set_member()

    response = client.put(f"/api/v1/helpers/tasks/{task['id']}/helpers/100")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to update helper tasks"
    }


def test_remove_helper() -> None:
    task = create_deadline_task(client, published=True)
    sign_up_helper(client, task["id"], member_id=100)
    FakeAuth.set_helpers_app_admin()

    response = client.delete(f"/api/v1/helpers/tasks/{task['id']}/helpers/100")

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
        captain_required_licence_info=None,
        helper_min_count=1,
        helper_max_count=2,
        published=True,
        captain=None,
        helpers=[],
    )


def test_remove_helper_fails_if_helper_not_on_task() -> None:
    task = create_deadline_task(client, published=True)
    FakeAuth.set_helpers_app_admin()

    response = client.delete(f"/api/v1/helpers/tasks/{task['id']}/helpers/100")

    assert response.status_code == 404
    assert response.json() == {"detail": "Helper is not on the task"}


def test_remove_helper_fails_if_not_editor_or_admin() -> None:
    task = create_deadline_task(client, published=True)
    FakeAuth.set_member()

    response = client.delete(f"/api/v1/helpers/tasks/{task['id']}/helpers/100")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to update helper tasks"
    }


# ==============================================================================
# Mark As Done
# ==============================================================================


def test_mark_as_done() -> None:
    FakeAuth.set_helpers_app_admin()

    response = client.post(
        "/api/v1/helpers/tasks/2011/mark-as-done",
        json={"comment": "All good"},
    )

    assert response.status_code == 200
    assert_task_json(
        response.json(),
        category=CATEGORY_MAINTENANCE,
        title="Winter Maintenance J80",
        short_description="Go to BA5 and do something",
        long_description=None,
        contact=MEMBER_1,
        starts_at="2026-01-04T15:00:00",
        ends_at="2026-01-04T18:00:00",
        deadline=None,
        urgent=False,
        captain_required_licence_info=None,
        helper_min_count=1,
        helper_max_count=2,
        published=True,
        captain=None,
        helpers=[],
        marked_as_done_at=ANY,
        marked_as_done_by=MEMBER_1,
        marked_as_done_comment="<p>All good</p>",
    )


def test_mark_as_done_with_no_comment() -> None:
    task = create_deadline_task(
        client,
        published=True,
        deadline=f"{past_day}T20:00:00",
    )
    FakeAuth.set_helpers_app_admin()

    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/mark-as-done",
        json={"comment": None},
    )

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
    )


def test_mark_as_done_fails_if_already_done() -> None:
    task = create_deadline_task(
        client,
        published=True,
        deadline=f"{past_day}T20:00:00",
    )
    FakeAuth.set_helpers_app_admin()
    done_resp = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/mark-as-done",
        json={"comment": None},
    )
    assert done_resp.status_code == 200
    assert isinstance(done_resp.json()["markedAsDoneAt"], str)

    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/mark-as-done",
        json={"comment": None},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Task already marked as done"}


def test_mark_as_done_fails_if_task_in_the_future() -> None:
    task = create_shift_task(client, published=True)
    FakeAuth.set_helpers_app_admin()

    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/mark-as-done",
        json={"comment": None},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot mark a task as done before it starts"}


def test_mark_as_done_fails_if_not_admin_and_not_contact_or_captain() -> None:
    task = create_deadline_task(
        client,
        published=True,
        deadline=f"{past_day}T20:00:00",
    )
    FakeAuth.set_member()

    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/mark-as-done",
        json={"comment": None},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to mark this task as done"
    }


def test_mark_as_done_as_contact() -> None:
    task = create_deadline_task(
        client,
        published=True,
        contact_id=2,
        deadline=f"{past_day}T20:00:00",
    )
    FakeAuth.set_helpers_app_editor()  # editor = member 2 = contact

    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/mark-as-done",
        json={"comment": "Done by contact"},
    )

    assert response.status_code == 200
    assert_task_json(
        response.json(),
        category=CATEGORY_MAINTENANCE,
        title="Test Task",
        short_description="Test task description",
        long_description=None,
        contact=MEMBER_2,
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
        marked_as_done_by=MEMBER_2,
        marked_as_done_comment="<p>Done by contact</p>",
    )


# ==============================================================================
# Validate
# ==============================================================================


def test_validate() -> None:
    FakeAuth.set_helpers_app_admin()

    client.post(
        "/api/v1/helpers/tasks/2012/mark-as-done",
        json={"comment": "Done"},
    )

    response = client.post(
        "/api/v1/helpers/tasks/2012/validate",
        json={"comment": "Validated!"},
    )

    assert response.status_code == 200
    assert_task_json(
        response.json(),
        category=CATEGORY_MAINTENANCE,
        title="Winter Maintenance J70",
        short_description="Go to BA5 and do something",
        long_description=None,
        contact=MEMBER_1,
        starts_at=None,
        ends_at=None,
        deadline="2026-01-05T20:00:00",
        urgent=False,
        captain_required_licence_info=None,
        helper_min_count=2,
        helper_max_count=2,
        published=True,
        captain=helper_entry(1),
        helpers=[helper_entry(2), helper_entry(3)],
        marked_as_done_at=ANY,
        marked_as_done_by=MEMBER_1,
        marked_as_done_comment="<p>Done</p>",
        validated_at=ANY,
        validated_by=MEMBER_1,
        validation_comment="<p>Validated!</p>",
    )


def test_validate_without_prior_mark_as_done() -> None:
    task = create_deadline_task(
        client,
        published=True,
        deadline=f"{past_day}T20:00:00",
    )
    FakeAuth.set_helpers_app_admin()

    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/validate",
        json={"comment": None},
    )

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


def test_validate_fails_if_already_validated() -> None:
    task = create_deadline_task(
        client,
        published=True,
        deadline=f"{past_day}T20:00:00",
    )
    FakeAuth.set_helpers_app_admin()
    first_resp = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/validate",
        json={"comment": None},
    )
    assert first_resp.status_code == 200
    assert isinstance(first_resp.json()["validatedAt"], str)

    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/validate",
        json={"comment": None},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Task already validated"}


def test_validate_fails_if_task_in_the_future() -> None:
    task = create_shift_task(client, published=True)
    FakeAuth.set_helpers_app_admin()

    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/validate",
        json={"comment": None},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot validate a task before it starts"}


def test_validate_fails_if_not_admin_and_not_contact() -> None:
    task = create_deadline_task(
        client,
        published=True,
        deadline=f"{past_day}T20:00:00",
    )
    FakeAuth.set_member()

    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/validate",
        json={"comment": None},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to validate this task"
    }


def test_validate_unsets_urgent_for_validated_tasks() -> None:
    task = create_deadline_task(
        client,
        published=True,
        urgent=True,
        deadline=f"{past_day}T20:00:00",
    )
    FakeAuth.set_helpers_app_admin()

    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/validate",
        json={"comment": None},
    )

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
