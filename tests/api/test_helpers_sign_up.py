"""Helpers sign-up API tests."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from tests.api.conftest import client
from tests.api.helpers_test_utils import (
    assert_captain_shape,
    assert_full_task_response,
    assert_helper_shape,
    create_deadline_task,
    create_shift_task,
    create_surveillance_shift,
    verify_sign_up_audit_log,
)
from tests.main_test import FakeAuth
from ycc_hull.db.context import DatabaseContextHolder
from ycc_hull.db.entities import HelperTaskEntity, HelperTaskHelperEntity
from ycc_hull.utils import get_now

_HELPERS_MODULE = "ycc_hull.controllers.helpers_controller"

_current_year = get_now().year

# A fixed date before the surveillance sign-up cutoff (1 May)
_BEFORE_CUTOFF = datetime(_current_year, 3, 15, 12, 0, 0, tzinfo=UTC)
# A fixed date after the surveillance sign-up cutoff (1 May)
_AFTER_CUTOFF = datetime(_current_year, 6, 15, 12, 0, 0, tzinfo=UTC)

_current_july = f"{_current_year}-07-15"
_current_august = f"{_current_year}-08-15"

# ==============================================================================
# Sign Up As Helper - Happy Path
# ==============================================================================


def test_sign_up_as_helper() -> None:
    task = create_shift_task(client)
    FakeAuth.set_member()

    response = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")

    assert response.status_code == 200
    data = response.json()
    assert_full_task_response(data)
    assert data["id"] == task["id"]
    assert data["title"] == "Test Task"
    assert data["published"] is True
    assert data["captain"] is None
    assert len(data["helpers"]) == 1
    assert_helper_shape(data["helpers"][0], member_id=100)

    verify_sign_up_audit_log(task["id"], "SignUpAsHelper")


def test_sign_up_as_helper_deadline_task() -> None:
    task = create_deadline_task(client)
    FakeAuth.set_member()

    response = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")

    assert response.status_code == 200
    data = response.json()
    assert_full_task_response(data)
    assert data["id"] == task["id"]
    assert data["startsAt"] is None
    assert data["endsAt"] is None
    assert isinstance(data["deadline"], str)
    assert data["captain"] is None
    assert len(data["helpers"]) == 1
    assert_helper_shape(data["helpers"][0], member_id=100)

    verify_sign_up_audit_log(task["id"], "SignUpAsHelper")


def test_sign_up_as_helper_multiple_members() -> None:
    task = create_shift_task(client, helper_max_count=3)

    FakeAuth.set_member(member_id=100)
    response1 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")
    assert response1.status_code == 200
    data1 = response1.json()
    assert_full_task_response(data1)
    assert len(data1["helpers"]) == 1

    FakeAuth.set_member(member_id=101)
    response2 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")

    assert response2.status_code == 200
    data2 = response2.json()
    assert_full_task_response(data2)
    assert len(data2["helpers"]) == 2
    helper_ids = {h["member"]["id"] for h in data2["helpers"]}
    assert helper_ids == {100, 101}

    verify_sign_up_audit_log(task["id"], "SignUpAsHelper")


# ==============================================================================
# Sign Up As Helper - Shared Validation
# ==============================================================================


def test_sign_up_as_helper_fails_if_unpublished() -> None:
    task = create_shift_task(client, published=False)
    FakeAuth.set_member()

    response = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")

    # Unpublished tasks are invisible (filtered by published=True), so 404
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_sign_up_as_helper_fails_if_task_in_the_past() -> None:
    # Pre-seeded task 2001: starts previous year Jan 4, published, maintenance
    FakeAuth.set_member()

    response = client.post("/api/v1/helpers/tasks/2001/sign-up-as-helper")

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot sign up for a task in the past"}


def test_sign_up_as_helper_fails_if_already_signed_up_as_helper() -> None:
    task = create_shift_task(client)
    FakeAuth.set_member()

    response1 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")
    assert response1.status_code == 200

    response2 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")

    assert response2.status_code == 409
    assert response2.json() == {"detail": "Already signed up as helper"}


def test_sign_up_as_helper_fails_if_already_signed_up_as_captain() -> None:
    task = create_deadline_task(client)
    FakeAuth.set_member()

    response1 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain")
    assert response1.status_code == 200

    response2 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")

    assert response2.status_code == 409
    assert response2.json() == {"detail": "Already signed up as captain"}


def test_sign_up_as_helper_fails_if_task_not_found() -> None:
    FakeAuth.set_member()

    response = client.post("/api/v1/helpers/tasks/99999/sign-up-as-helper")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


# ==============================================================================
# Sign Up As Helper - Helper Limit
# ==============================================================================


def test_sign_up_as_helper_fails_if_limit_reached() -> None:
    task = create_shift_task(client, helper_max_count=1)

    FakeAuth.set_member(member_id=100)
    response1 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")
    assert response1.status_code == 200

    FakeAuth.set_member(member_id=101)
    response2 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")

    assert response2.status_code == 409
    assert response2.json() == {"detail": "Task helper limit reached"}


# ==============================================================================
# Sign Up As Helper - Surveillance Limit
# ==============================================================================


def test_sign_up_as_helper_surveillance_limit_first_is_ok() -> None:
    """First surveillance helper sign-up (before cutoff) should succeed."""
    task = create_surveillance_shift(client)
    FakeAuth.set_member(member_id=200)

    with patch(f"{_HELPERS_MODULE}.get_now", return_value=_BEFORE_CUTOFF):
        response = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")

    assert response.status_code == 200
    data = response.json()
    assert_full_task_response(data)
    assert data["category"]["title"] == "Surveillance"
    assert len(data["helpers"]) == 1
    assert_helper_shape(data["helpers"][0], member_id=200)

    verify_sign_up_audit_log(task["id"], "SignUpAsHelper")


def test_sign_up_as_helper_surveillance_limit_second_blocked() -> None:
    """Second surveillance helper sign-up (before cutoff) should be blocked.

    Regardless of task date.
    """
    task1 = create_surveillance_shift(client)
    task2 = create_surveillance_shift(
        client,
        starts_at=f"{_current_july}T10:00:00",
        ends_at=f"{_current_july}T18:00:00",
    )

    FakeAuth.set_member(member_id=201)
    with patch(f"{_HELPERS_MODULE}.get_now", return_value=_BEFORE_CUTOFF):
        response1 = client.post(
            f"/api/v1/helpers/tasks/{task1['id']}/sign-up-as-helper"
        )
        assert response1.status_code == 200

        response2 = client.post(
            f"/api/v1/helpers/tasks/{task2['id']}/sign-up-as-helper"
        )

    assert response2.status_code == 409
    assert response2.json() == {
        "detail": (
            "You cannot sign up for multiple surveillance shifts before 1 May "
            "- but you can still sign up for maintenance and other tasks! 😉"
        )
    }


def test_sign_up_as_helper_surveillance_limit_allowed_after_cutoff() -> None:
    """After the cutoff date, multiple surveillance sign-ups should be allowed."""
    task1 = create_surveillance_shift(
        client,
        starts_at=f"{_current_july}T10:00:00",
        ends_at=f"{_current_july}T18:00:00",
    )
    task2 = create_surveillance_shift(
        client,
        starts_at=f"{_current_august}T10:00:00",
        ends_at=f"{_current_august}T18:00:00",
    )

    FakeAuth.set_member(member_id=202)
    with patch(f"{_HELPERS_MODULE}.get_now", return_value=_AFTER_CUTOFF):
        response1 = client.post(
            f"/api/v1/helpers/tasks/{task1['id']}/sign-up-as-helper"
        )
        assert response1.status_code == 200

        response2 = client.post(
            f"/api/v1/helpers/tasks/{task2['id']}/sign-up-as-helper"
        )

    assert response2.status_code == 200
    data = response2.json()
    assert_full_task_response(data)
    assert data["category"]["title"] == "Surveillance"
    assert len(data["helpers"]) == 1
    assert_helper_shape(data["helpers"][0], member_id=202)


def test_sign_up_helper_surveillance_limit_does_not_block_maintenance() -> None:
    """Surveillance limit should not block signing up for maintenance tasks."""
    surveillance_task = create_surveillance_shift(client)
    maintenance_task = create_shift_task(client)

    FakeAuth.set_member(member_id=203)
    with patch(f"{_HELPERS_MODULE}.get_now", return_value=_BEFORE_CUTOFF):
        response1 = client.post(
            f"/api/v1/helpers/tasks/{surveillance_task['id']}/sign-up-as-helper"
        )
        assert response1.status_code == 200

        response2 = client.post(
            f"/api/v1/helpers/tasks/{maintenance_task['id']}/sign-up-as-helper"
        )

    assert response2.status_code == 200
    data = response2.json()
    assert_full_task_response(data)
    assert data["category"]["title"] == "Maintenance / General"
    assert len(data["helpers"]) == 1
    assert_helper_shape(data["helpers"][0], member_id=203)

    verify_sign_up_audit_log(maintenance_task["id"], "SignUpAsHelper")


def test_sign_up_as_helper_surveillance_different_members() -> None:
    """Different members should each be able to sign up for the same surveillance task.

    Verifies the limit is per-member, not global.
    """
    task = create_surveillance_shift(client)

    with patch(f"{_HELPERS_MODULE}.get_now", return_value=_BEFORE_CUTOFF):
        FakeAuth.set_member(member_id=205)
        response1 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")
        assert response1.status_code == 200
        data1 = response1.json()
        assert_full_task_response(data1)
        assert len(data1["helpers"]) == 1

        FakeAuth.set_member(member_id=206)
        response2 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")

    assert response2.status_code == 200
    data2 = response2.json()
    assert_full_task_response(data2)
    assert len(data2["helpers"]) == 2
    helper_ids = {h["member"]["id"] for h in data2["helpers"]}
    assert helper_ids == {205, 206}

    verify_sign_up_audit_log(task["id"], "SignUpAsHelper")


def test_sign_up_as_captain_surveillance_limit_not_restricted() -> None:
    """Captains (drivers) are not subject to the surveillance sign-up limit."""
    task1 = create_surveillance_shift(client)
    task2 = create_surveillance_shift(client)

    FakeAuth.set_member(member_id=4)  # member 4 has active licence 9
    with patch(f"{_HELPERS_MODULE}.get_now", return_value=_BEFORE_CUTOFF):
        response1 = client.post(
            f"/api/v1/helpers/tasks/{task1['id']}/sign-up-as-captain"
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert_full_task_response(data1)
        assert_captain_shape(data1["captain"], member_id=4)

        response2 = client.post(
            f"/api/v1/helpers/tasks/{task2['id']}/sign-up-as-captain"
        )

    assert response2.status_code == 200
    data2 = response2.json()
    assert_full_task_response(data2)
    assert_captain_shape(data2["captain"], member_id=4)

    verify_sign_up_audit_log(task2["id"], "SignUpAsCaptain")


def test_sign_up_as_helper_surveillance_limit_previous_year_does_not_count() -> None:
    """Previous-year sign-ups should not count toward current year limit."""
    member_id = 207
    with DatabaseContextHolder.context.session() as session:
        prev_year_task = HelperTaskEntity(
            category_id=1,
            title="Surveillance",
            short_description="Previous year surveillance",
            contact_id=1,
            starts_at=datetime(_current_year - 1, 6, 1, 10, 0, 0, tzinfo=UTC),
            ends_at=datetime(_current_year - 1, 6, 1, 18, 0, 0, tzinfo=UTC),
            urgent=False,
            helper_min_count=1,
            helper_max_count=2,
            published=True,
            captain_required_licence_info_id=9,
        )
        session.add(prev_year_task)
        session.flush()
        session.add(
            HelperTaskHelperEntity(
                task_id=prev_year_task.id,
                member_id=member_id,
                signed_up_at=datetime(_current_year - 1, 6, 1, 10, 0, 0, tzinfo=UTC),
            )
        )
        session.commit()

    task = create_surveillance_shift(client)
    FakeAuth.set_member(member_id=member_id)

    with patch(f"{_HELPERS_MODULE}.get_now", return_value=_BEFORE_CUTOFF):
        response = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")

    assert response.status_code == 200
    data = response.json()
    assert_full_task_response(data)
    assert data["category"]["title"] == "Surveillance"
    assert len(data["helpers"]) == 1
    assert_helper_shape(data["helpers"][0], member_id=member_id)

    verify_sign_up_audit_log(task["id"], "SignUpAsHelper")


# ==============================================================================
# Sign Up As Captain - Happy Path
# ==============================================================================


def test_sign_up_as_captain() -> None:
    task = create_deadline_task(client)
    FakeAuth.set_member()

    response = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain")

    assert response.status_code == 200
    data = response.json()
    assert_full_task_response(data)
    assert data["id"] == task["id"]
    assert data["helpers"] == []
    assert_captain_shape(data["captain"], member_id=100)

    verify_sign_up_audit_log(task["id"], "SignUpAsCaptain")


def test_sign_up_as_captain_surveillance_with_licence() -> None:
    """Member with motor boat licence (id=9) can captain a surveillance task."""
    task = create_surveillance_shift(client)
    FakeAuth.set_member(member_id=4)  # member 4 has active licence 9

    response = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain")

    assert response.status_code == 200
    data = response.json()
    assert_full_task_response(data)
    assert data["category"]["title"] == "Surveillance"
    assert isinstance(data["captainRequiredLicenceInfo"], dict)
    assert data["captainRequiredLicenceInfo"]["id"] == 9
    assert data["helpers"] == []
    assert_captain_shape(data["captain"], member_id=4)

    verify_sign_up_audit_log(task["id"], "SignUpAsCaptain")


def test_sign_up_as_captain_no_licence_required() -> None:
    """Task without licence requirement should allow any member as captain."""
    task = create_shift_task(client, captain_required_licence_info_id=None)
    FakeAuth.set_member()

    response = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain")

    assert response.status_code == 200
    data = response.json()
    assert_full_task_response(data)
    assert data["captainRequiredLicenceInfo"] is None
    assert data["helpers"] == []
    assert_captain_shape(data["captain"], member_id=100)

    verify_sign_up_audit_log(task["id"], "SignUpAsCaptain")


# ==============================================================================
# Sign Up As Captain - Shared Validation
# ==============================================================================


def test_sign_up_as_captain_fails_if_unpublished() -> None:
    task = create_deadline_task(client, published=False)
    FakeAuth.set_member()

    response = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found or not published"}


def test_sign_up_as_captain_fails_if_task_in_the_past() -> None:
    FakeAuth.set_member()

    response = client.post("/api/v1/helpers/tasks/2001/sign-up-as-captain")

    assert response.status_code == 409
    assert response.json() == {"detail": "Cannot sign up for a task in the past"}


def test_sign_up_as_captain_fails_if_already_signed_up_as_captain() -> None:
    task = create_deadline_task(client)

    FakeAuth.set_member(member_id=100)
    response1 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain")
    assert response1.status_code == 200

    response2 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain")

    assert response2.status_code == 409
    assert response2.json() == {"detail": "Already signed up as captain"}


def test_sign_up_as_captain_fails_if_already_signed_up_as_helper() -> None:
    task = create_deadline_task(client)

    FakeAuth.set_member(member_id=100)
    response1 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper")
    assert response1.status_code == 200

    response2 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain")

    assert response2.status_code == 409
    assert response2.json() == {"detail": "Already signed up as helper"}


def test_sign_up_as_captain_fails_if_task_not_found() -> None:
    FakeAuth.set_member()

    response = client.post("/api/v1/helpers/tasks/99999/sign-up-as-captain")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found or not published"}


# ==============================================================================
# Sign Up As Captain - Captain-Specific Validation
# ==============================================================================


def test_sign_up_as_captain_fails_if_already_has_captain() -> None:
    task = create_deadline_task(client)

    FakeAuth.set_member(member_id=100)
    response1 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain")
    assert response1.status_code == 200

    FakeAuth.set_member(member_id=101)
    response2 = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain")

    assert response2.status_code == 409
    assert response2.json() == {"detail": "Task already has a captain"}


def test_sign_up_as_captain_fails_without_required_licence() -> None:
    """Member without motor boat licence cannot captain a surveillance task."""
    task = create_surveillance_shift(client)
    FakeAuth.set_member(member_id=100)  # member 100 does NOT have licence 9

    response = client.post(f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain")

    assert response.status_code == 409
    assert response.json() == {"detail": "Task captain needs licence: M"}


# ==============================================================================
# Sign-up blocked by workflow state
# ==============================================================================


def test_sign_up_as_helper_fails_if_task_marked_as_done() -> None:
    past_shift_start = (get_now().date() - timedelta(days=2)).strftime("%Y-%m-%d")
    task = create_shift_task(
        client,
        published=True,
        starts_at=f"{past_shift_start}T10:00:00",
        ends_at=f"{past_shift_start}T18:00:00",
    )
    FakeAuth.set_helpers_app_admin()
    done_resp = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/mark-as-done",
        json={"comment": None},
    )
    assert done_resp.status_code == 200
    assert isinstance(done_resp.json()["markedAsDoneAt"], str)

    FakeAuth.set_member()
    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-helper",
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Cannot sign up for a task marked as done",
    }


def test_sign_up_as_captain_fails_if_task_validated() -> None:
    past_shift_start = (get_now().date() - timedelta(days=2)).strftime("%Y-%m-%d")
    task = create_shift_task(
        client,
        published=True,
        starts_at=f"{past_shift_start}T10:00:00",
        ends_at=f"{past_shift_start}T18:00:00",
    )
    FakeAuth.set_helpers_app_admin()
    validate_resp = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/validate",
        json={"comment": None},
    )
    assert validate_resp.status_code == 200
    assert isinstance(validate_resp.json()["validatedAt"], str)

    FakeAuth.set_member()
    response = client.post(
        f"/api/v1/helpers/tasks/{task['id']}/sign-up-as-captain",
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Cannot sign up for a validated task",
    }
