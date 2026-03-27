"""Helpers permissions API tests."""

import json

import pytest

from tests.api.conftest import client
from tests.api.helpers_test_utils import get_last_audit_log_entry
from tests.main_test import FakeAuth

# ==============================================================================
# Authorization - only admin can manage permissions
# ==============================================================================


def test_get_permissions_fails_if_not_admin() -> None:
    FakeAuth.set_member()

    response = client.get("/api/v1/helpers/permissions")

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_get_permissions_fails_if_editor() -> None:
    FakeAuth.set_helpers_app_editor()

    response = client.get("/api/v1/helpers/permissions")

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_grant_permission_fails_if_not_admin() -> None:
    FakeAuth.set_member()

    response = client.post(
        "/api/v1/helpers/permissions",
        json={"memberId": 100, "permission": "EDITOR", "note": None},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_grant_permission_fails_if_editor() -> None:
    FakeAuth.set_helpers_app_editor()

    response = client.post(
        "/api/v1/helpers/permissions",
        json={"memberId": 100, "permission": "EDITOR", "note": None},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_update_permission_fails_if_not_admin() -> None:
    FakeAuth.set_member()

    response = client.put(
        "/api/v1/helpers/permissions/2",
        json={"note": "Updated"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_update_permission_fails_if_editor() -> None:
    FakeAuth.set_helpers_app_editor()

    response = client.put(
        "/api/v1/helpers/permissions/2",
        json={"note": "Updated"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_revoke_permission_fails_if_not_admin() -> None:
    FakeAuth.set_member()

    response = client.delete("/api/v1/helpers/permissions/2")

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


def test_revoke_permission_fails_if_editor() -> None:
    FakeAuth.set_helpers_app_editor()

    response = client.delete("/api/v1/helpers/permissions/2")

    assert response.status_code == 403
    assert response.json() == {"detail": "Forbidden"}


# ==============================================================================
# GET - List all permissions
# ==============================================================================


def test_get_permissions() -> None:
    FakeAuth.set_helpers_app_admin()

    response = client.get("/api/v1/helpers/permissions")

    assert response.status_code == 200
    permissions = response.json()
    # Seed data: member 1 (ADMIN), member 2 (EDITOR), member 3 (EDITOR)
    assert len(permissions) == 3
    permission_map = {p["member"]["id"]: p for p in permissions}
    assert permission_map[1]["permission"] == "ADMIN"
    assert permission_map[2]["permission"] == "EDITOR"
    assert permission_map[3]["permission"] == "EDITOR"


def test_get_permissions_returns_notes() -> None:
    FakeAuth.set_helpers_app_admin()

    response = client.get("/api/v1/helpers/permissions")

    assert response.status_code == 200
    permission_map = {p["member"]["id"]: p for p in response.json()}
    assert permission_map[1]["note"] == "Admin"
    assert permission_map[2]["note"] == "Y Coordinator"
    assert permission_map[3]["note"] is None


# ==============================================================================
# POST - Grant permission
# ==============================================================================


@pytest.mark.asyncio
async def test_grant_permission() -> None:
    FakeAuth.set_helpers_app_admin()

    response = client.post(
        "/api/v1/helpers/permissions",
        json={"memberId": 4, "permission": "EDITOR", "note": "New editor"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["member"]["id"] == 4
    assert data["permission"] == "EDITOR"
    assert data["note"] == "New editor"

    # Verify audit log
    audit = get_last_audit_log_entry()
    assert audit.application.startswith("YCC Hull")
    assert audit.principal == "testuser"
    assert audit.description == "Helpers/Permissions/Grant"
    assert isinstance(audit.data, str)
    audit_data = json.loads(audit.data)
    assert audit_data.keys() == {"new"}


@pytest.mark.asyncio
async def test_grant_permission_without_note() -> None:
    FakeAuth.set_helpers_app_admin()

    response = client.post(
        "/api/v1/helpers/permissions",
        json={"memberId": 5, "permission": "EDITOR", "note": None},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["member"]["id"] == 5
    assert data["permission"] == "EDITOR"
    assert data["note"] is None


def test_grant_permission_shows_up_in_list() -> None:
    FakeAuth.set_helpers_app_admin()

    # Grant
    grant_response = client.post(
        "/api/v1/helpers/permissions",
        json={"memberId": 6, "permission": "EDITOR", "note": "Temp"},
    )
    assert grant_response.status_code == 200

    # Verify it appears in the list
    list_response = client.get("/api/v1/helpers/permissions")
    assert list_response.status_code == 200
    member_ids = {p["member"]["id"] for p in list_response.json()}
    assert 6 in member_ids


# ==============================================================================
# PUT - Update permission
# ==============================================================================


@pytest.mark.asyncio
async def test_update_permission_note() -> None:
    FakeAuth.set_helpers_app_admin()

    # Update the note for member 3 (seeded EDITOR with no note)
    response = client.put(
        "/api/v1/helpers/permissions/3",
        json={"note": "Updated note"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["member"]["id"] == 3
    assert data["note"] == "Updated note"

    # Verify audit log
    audit = get_last_audit_log_entry()
    assert audit.principal == "testuser"
    assert audit.description == "Helpers/Permissions/Update/3"
    assert isinstance(audit.data, str)
    audit_data = json.loads(audit.data)
    assert audit_data.keys() == {"diff", "old", "new"}


@pytest.mark.asyncio
async def test_update_permission_clear_note() -> None:
    FakeAuth.set_helpers_app_admin()

    # First set a note
    client.put(
        "/api/v1/helpers/permissions/3",
        json={"note": "Temporary note"},
    )

    # Then clear it
    response = client.put(
        "/api/v1/helpers/permissions/3",
        json={"note": None},
    )

    assert response.status_code == 200
    assert response.json()["note"] is None


def test_update_permission_not_found() -> None:
    FakeAuth.set_helpers_app_admin()

    response = client.put(
        "/api/v1/helpers/permissions/99999",
        json={"note": "Does not exist"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Permission not found"}


# ==============================================================================
# DELETE - Revoke permission
# ==============================================================================


@pytest.mark.asyncio
async def test_revoke_permission() -> None:
    FakeAuth.set_helpers_app_admin()

    # Grant a permission first so we can revoke it
    client.post(
        "/api/v1/helpers/permissions",
        json={"memberId": 7, "permission": "EDITOR", "note": "To be revoked"},
    )

    response = client.delete("/api/v1/helpers/permissions/7")

    assert response.status_code == 204

    # Verify audit log
    audit = get_last_audit_log_entry()
    assert audit.principal == "testuser"
    assert audit.description == "Helpers/Permissions/Revoke/7"
    assert isinstance(audit.data, str)
    audit_data = json.loads(audit.data)
    assert audit_data.keys() == {"old"}


def test_revoke_permission_no_longer_in_list() -> None:
    FakeAuth.set_helpers_app_admin()

    # Grant then revoke
    client.post(
        "/api/v1/helpers/permissions",
        json={"memberId": 8, "permission": "EDITOR", "note": None},
    )
    assert client.delete("/api/v1/helpers/permissions/8").status_code == 204

    # Verify it's gone
    list_response = client.get("/api/v1/helpers/permissions")
    member_ids = {p["member"]["id"] for p in list_response.json()}
    assert 8 not in member_ids


def test_revoke_own_permission_fails() -> None:
    """Admin (member_id=1) cannot revoke their own permission."""
    FakeAuth.set_helpers_app_admin()

    response = client.delete("/api/v1/helpers/permissions/1")

    assert response.status_code == 409
    assert response.json() == {"detail": "You cannot revoke your own permissions"}


def test_revoke_permission_not_found() -> None:
    FakeAuth.set_helpers_app_admin()

    response = client.delete("/api/v1/helpers/permissions/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Permission not found"}
