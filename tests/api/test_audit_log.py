from datetime import timedelta

from tests.api.conftest import client
from tests.main_test import FakeAuth
from ycc_hull.db.context import DatabaseContextHolder
from ycc_hull.db.entities import AuditLogEntryEntity
from ycc_hull.utils import get_now


def _seed_audit_log_entries() -> list[int]:
    now = get_now()
    with DatabaseContextHolder.context.session() as session:
        entries = [
            AuditLogEntryEntity(
                application="test-app",
                principal="testuser",
                description="Action one",
                data='{"key": "value1"}',
                created_at=now - timedelta(hours=2),
            ),
            AuditLogEntryEntity(
                application="test-app",
                principal="testuser",
                description="Action two",
                data='{"key": "value2"}',
                created_at=now - timedelta(hours=1),
            ),
            AuditLogEntryEntity(
                application="test-app",
                principal="other-user",
                description="Old action",
                data=None,
                created_at=now,
            ),
        ]
        session.add_all(entries)
        session.commit()
        return [e.id for e in entries]


def _clear_audit_log() -> None:
    with DatabaseContextHolder.context.session() as session:
        session.query(AuditLogEntryEntity).delete()
        session.commit()


# ==============================================================================
# GET /api/v1/audit-log/entries
# ==============================================================================


def test_audit_log_entries_get_as_admin() -> None:
    _clear_audit_log()
    ids = _seed_audit_log_entries()
    FakeAuth.set_helpers_app_admin()

    response = client.get("/api/v1/audit-log/entries")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # List endpoint omits data, sorted by createdAt descending
    created_ats = [e["createdAt"] for e in data]
    assert created_ats == sorted(created_ats, reverse=True)

    # Most recent entry (last seeded) is first
    assert data[0]["id"] == ids[2]
    assert data[0]["application"] == "test-app"
    assert data[0]["principal"] == "other-user"
    assert data[0]["description"] == "Old action"
    assert data[0]["data"] is None


def test_audit_log_entries_get_forbidden_for_member() -> None:
    FakeAuth.set_member()

    response = client.get("/api/v1/audit-log/entries")

    assert response.status_code == 403


# ==============================================================================
# GET /api/v1/audit-log/entries/{id}  # noqa: ERA001
# ==============================================================================


def test_audit_log_entry_get_by_id() -> None:
    _clear_audit_log()
    ids = _seed_audit_log_entries()
    FakeAuth.set_helpers_app_admin()

    response = client.get(f"/api/v1/audit-log/entries/{ids[0]}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == ids[0]
    assert data["application"] == "test-app"
    assert data["principal"] == "testuser"
    assert data["description"] == "Action one"
    assert data["data"] == '{"key": "value1"}'


def test_audit_log_entry_get_by_id_not_found() -> None:
    FakeAuth.set_helpers_app_admin()

    response = client.get("/api/v1/audit-log/entries/999999")

    assert response.status_code == 404


def test_audit_log_entry_get_by_id_forbidden_for_member() -> None:
    FakeAuth.set_member()

    response = client.get("/api/v1/audit-log/entries/1")

    assert response.status_code == 403


# ==============================================================================
# DELETE /api/v1/audit-log/entries
# ==============================================================================


def test_audit_log_entries_delete() -> None:
    _clear_audit_log()
    _seed_audit_log_entries()
    FakeAuth.set_helpers_app_admin()

    # Delete entries older than tomorrow (should delete all)
    tomorrow = (get_now().date() + timedelta(days=1)).isoformat()
    response = client.request(
        "DELETE",
        "/api/v1/audit-log/entries",
        json={"cutoffDate": tomorrow},
    )

    assert response.status_code == 204

    # Verify all 3 seeded entries were deleted.
    # The delete action itself logs an audit entry via a background task, so 0 or 1
    # entries may be present
    response = client.get("/api/v1/audit-log/entries")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 1


def test_audit_log_entries_delete_forbidden_for_member() -> None:
    FakeAuth.set_member()

    response = client.request(
        "DELETE",
        "/api/v1/audit-log/entries",
        json={"cutoffDate": "2025-01-01"},
    )

    assert response.status_code == 403
