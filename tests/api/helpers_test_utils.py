import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select

from tests.main_test import FakeAuth
from ycc_hull.db.context import DatabaseContextHolder
from ycc_hull.db.entities import AuditLogEntryEntity
from ycc_hull.utils import get_now

# ==============================================================================
# ANY sentinel (equals anything - used for dynamic fields in assertions)
# ==============================================================================


class _Any:
    """Sentinel that equals anything."""

    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return "<ANY>"


ANY = _Any()

# ==============================================================================
# Response-shape key sets
# ==============================================================================

TASK_RESPONSE_KEYS = {
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
}

CATEGORY_RESPONSE_KEYS = {"id", "title", "shortDescription", "longDescription"}

MEMBER_PUBLIC_INFO_KEYS = {
    "id",
    "username",
    "firstName",
    "lastName",
    "email",
    "mobilePhone",
    "homePhone",
    "workPhone",
}

HELPER_KEYS = {"member", "signedUpAt"}

AUDIT_TASK_KEYS = {"@type", *TASK_RESPONSE_KEYS}

# ==============================================================================
# Well-known seed data dicts (loaded from generated test data)
# ==============================================================================

_GENERATED_DIR = (
    Path(__file__).resolve().parent.parent.parent / "test_data" / "generated"
)


def _load_member(member_id: int) -> dict[str, Any]:
    with (_GENERATED_DIR / "Members.json").open(encoding="utf-8") as f:
        members = json.load(f)
    with (_GENERATED_DIR / "Users.json").open(encoding="utf-8") as f:
        users = json.load(f)

    member = next(m for m in members if m["id"] == member_id)
    user = next(u for u in users if u["member_id"] == member_id)

    return {
        "id": member_id,
        "username": user["logon_id"],
        "firstName": member["firstname"],
        "lastName": member["name"],
        "email": member["e_mail"],
        "mobilePhone": member["cell_phone"],
        "homePhone": member["home_phone"],
        "workPhone": member["work_phone"],
    }


MEMBER_1 = _load_member(1)
MEMBER_2 = _load_member(2)

CATEGORY_SURVEILLANCE = {
    "id": 1,
    "title": "Surveillance",
    "shortDescription": "Q-boat surveillance",
    "longDescription": None,
}

CATEGORY_MAINTENANCE = {
    "id": 2,
    "title": "Maintenance / General",
    "shortDescription": "General maintenance",
    "longDescription": None,
}

# ==============================================================================
# Computed dates
# ==============================================================================

future_day = (get_now().date() + timedelta(days=5)).strftime("%Y-%m-%d")
past_day = (get_now().date() - timedelta(days=1)).strftime("%Y-%m-%d")

# ==============================================================================
# Task creation helpers
# ==============================================================================


def create_task(  # noqa: PLR0913
    client: TestClient,
    *,
    category_id: int = 2,
    starts_at: str | None = None,
    ends_at: str | None = None,
    deadline: str | None = None,
    published: bool = True,
    captain_required_licence_info_id: int | None = None,
    helper_min_count: int = 1,
    helper_max_count: int = 2,
    contact_id: int = 1,
    urgent: bool = False,
) -> dict:
    FakeAuth.set_helpers_app_admin()
    request = {
        "categoryId": category_id,
        "title": "Test Task",
        "shortDescription": "Test task description",
        "longDescription": None,
        "contactId": contact_id,
        "startsAt": starts_at,
        "endsAt": ends_at,
        "deadline": deadline,
        "urgent": urgent,
        "captainRequiredLicenceInfoId": captain_required_licence_info_id,
        "helperMinCount": helper_min_count,
        "helperMaxCount": helper_max_count,
        "published": published,
    }
    response = client.post("/api/v1/helpers/tasks", json=request)
    assert response.status_code == 200
    return response.json()


def create_shift_task(  # noqa: PLR0913
    client: TestClient,
    *,
    published: bool = True,
    starts_at: str = f"{future_day}T10:00:00",
    ends_at: str = f"{future_day}T18:00:00",
    helper_max_count: int = 2,
    captain_required_licence_info_id: int | None = None,
) -> dict:
    return create_task(
        client,
        published=published,
        starts_at=starts_at,
        ends_at=ends_at,
        helper_max_count=helper_max_count,
        captain_required_licence_info_id=captain_required_licence_info_id,
    )


def create_deadline_task(  # noqa: PLR0913
    client: TestClient,
    *,
    published: bool = True,
    deadline: str = f"{future_day}T20:00:00",
    urgent: bool = False,
    helper_max_count: int = 2,
    contact_id: int = 1,
) -> dict:
    return create_task(
        client,
        published=published,
        deadline=deadline,
        urgent=urgent,
        helper_max_count=helper_max_count,
        contact_id=contact_id,
    )


def create_surveillance_shift(
    client: TestClient,
    *,
    starts_at: str = f"{future_day}T10:00:00",
    ends_at: str = f"{future_day}T18:00:00",
) -> dict:
    return create_task(
        client,
        category_id=1,
        captain_required_licence_info_id=9,
        starts_at=starts_at,
        ends_at=ends_at,
    )


# ==============================================================================
# Sign-up helpers
# ==============================================================================


def sign_up_helper(client: TestClient, task_id: int, member_id: int = 100) -> dict:
    FakeAuth.set_member(member_id=member_id)
    resp = client.post(f"/api/v1/helpers/tasks/{task_id}/sign-up-as-helper")
    assert resp.status_code == 200
    data = resp.json()
    helper_ids = [h["member"]["id"] for h in data["helpers"]]
    assert member_id in helper_ids, f"member {member_id} not in helpers: {helper_ids}"
    return data


def sign_up_captain(client: TestClient, task_id: int, member_id: int = 100) -> dict:
    FakeAuth.set_member(member_id=member_id)
    resp = client.post(f"/api/v1/helpers/tasks/{task_id}/sign-up-as-captain")
    assert resp.status_code == 200
    data = resp.json()
    assert data["captain"] is not None, "captain is None after sign-up"
    assert data["captain"]["member"]["id"] == member_id
    return data


# ==============================================================================
# Update request builder
# ==============================================================================


def update_request_from(task: dict, **overrides: object) -> dict:
    request = {
        "categoryId": task["category"]["id"],
        "title": task["title"],
        "shortDescription": task["shortDescription"],
        "longDescription": task.get("longDescription"),
        "contactId": task["contact"]["id"],
        "startsAt": task["startsAt"],
        "endsAt": task["endsAt"],
        "deadline": task["deadline"],
        "urgent": task["urgent"],
        "captainRequiredLicenceInfoId": (
            task["captainRequiredLicenceInfo"]["id"]
            if task.get("captainRequiredLicenceInfo")
            else None
        ),
        "helperMinCount": task["helperMinCount"],
        "helperMaxCount": task["helperMaxCount"],
        "published": task["published"],
        "notifySignedUpMembers": False,
    }
    request.update(overrides)
    return request


# ==============================================================================
# Audit log helpers
# ==============================================================================


def get_last_audit_log_entry() -> AuditLogEntryEntity:
    with DatabaseContextHolder.context.session() as session:
        entry = session.scalar(
            select(AuditLogEntryEntity).order_by(AuditLogEntryEntity.id.desc()).limit(1)
        )
        if not entry:
            msg = "No audit log entry found"
            raise AssertionError(msg)
        return entry


def verify_creation_audit_log_entry(short_description: str) -> None:
    audit = get_last_audit_log_entry()
    assert audit.application.startswith("YCC Hull")
    assert audit.principal == "testuser"
    assert audit.description == "Helpers/Tasks/Create"
    assert isinstance(audit.data, str)

    audit_data = json.loads(audit.data)
    assert audit_data.keys() == {"new"}

    assert audit_data["new"]["@type"] == "ycc_hull.models.helpers_dtos.HelperTaskDto"
    assert audit_data["new"]["shortDescription"] == short_description
    assert audit_data["new"].keys() == AUDIT_TASK_KEYS


def verify_update_audit_log_entry(
    task_id: int, old_short_description: str, new_short_description: str
) -> None:
    audit = get_last_audit_log_entry()
    assert audit.application.startswith("YCC Hull")
    assert audit.principal == "testuser"
    assert audit.description == f"Helpers/Tasks/Update/{task_id}"
    assert isinstance(audit.data, str)

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
    assert audit_data["old"].keys() == AUDIT_TASK_KEYS

    assert audit_data["new"]["@type"] == "ycc_hull.models.helpers_dtos.HelperTaskDto"
    assert audit_data["new"]["id"] == task_id
    assert audit_data["new"]["shortDescription"] == new_short_description
    assert audit_data["new"].keys() == AUDIT_TASK_KEYS


def verify_sign_up_audit_log(task_id: int, action: str) -> None:
    expected_description = f"Helpers/Tasks/{action}/{task_id}"
    with DatabaseContextHolder.context.session() as session:
        entry = session.scalar(
            select(AuditLogEntryEntity).where(
                AuditLogEntryEntity.description == expected_description
            )
        )
        assert entry is not None, f"No audit log entry found for {expected_description}"
        assert entry.application.startswith("YCC Hull")
        assert entry.principal == "testuser"
        assert entry.data is None


# ==============================================================================
# Response shape assertions
# ==============================================================================


def assert_full_task_response(data: dict) -> None:
    assert data.keys() == TASK_RESPONSE_KEYS
    assert data["category"].keys() == CATEGORY_RESPONSE_KEYS
    assert data["contact"].keys() == MEMBER_PUBLIC_INFO_KEYS
    assert data["markedAsDoneAt"] is None
    assert data["markedAsDoneBy"] is None
    assert data["markedAsDoneComment"] is None
    assert data["validatedAt"] is None
    assert data["validatedBy"] is None
    assert data["validationComment"] is None


def helper_entry(member_id: int) -> dict[str, Any]:
    return {"member": {"id": member_id}, "signedUpAt": ANY}


def _assert_dict_subset(actual: dict, expected: dict, *, path: str) -> None:
    for sub_key, sub_value in expected.items():
        assert sub_key in actual, f"{path} missing key {sub_key!r}: {actual}"
        act = actual[sub_key]
        if isinstance(sub_value, dict) and isinstance(act, dict):
            _assert_dict_subset(act, sub_value, path=f"{path}[{sub_key!r}]")
        else:
            assert act == sub_value, f"{path}[{sub_key!r}]: {act!r} != {sub_value!r}"


def assert_task_json(  # noqa: PLR0913
    data: dict,
    *,
    category: dict,
    title: str,
    short_description: str,
    long_description: str | None,
    contact: dict,
    starts_at: str | None,
    ends_at: str | None,
    deadline: str | None,
    urgent: bool,
    captain_required_licence_info: dict | None,
    helper_min_count: int,
    helper_max_count: int,
    published: bool,
    captain: dict | None,
    helpers: list[dict],
    marked_as_done_at: str | _Any | None = None,
    marked_as_done_by: dict | None = None,
    marked_as_done_comment: str | None = None,
    validated_at: str | _Any | None = None,
    validated_by: dict | None = None,
    validation_comment: str | None = None,
) -> None:
    assert data.keys() == TASK_RESPONSE_KEYS

    # Verify nested shapes
    assert data["category"].keys() == CATEGORY_RESPONSE_KEYS
    assert data["contact"].keys() == MEMBER_PUBLIC_INFO_KEYS
    if data["captain"] is not None:
        assert data["captain"].keys() == HELPER_KEYS
        assert data["captain"]["member"].keys() == MEMBER_PUBLIC_INFO_KEYS
    for helper in data["helpers"]:
        assert helper.keys() == HELPER_KEYS
        assert helper["member"].keys() == MEMBER_PUBLIC_INFO_KEYS

    # Check every field
    expected: dict[str, object] = {
        "category": category,
        "title": title,
        "shortDescription": short_description,
        "longDescription": long_description,
        "contact": contact,
        "startsAt": starts_at,
        "endsAt": ends_at,
        "deadline": deadline,
        "urgent": urgent,
        "captainRequiredLicenceInfo": captain_required_licence_info,
        "helperMinCount": helper_min_count,
        "helperMaxCount": helper_max_count,
        "published": published,
        "captain": captain,
        "helpers": helpers,
        "markedAsDoneAt": marked_as_done_at,
        "markedAsDoneBy": marked_as_done_by,
        "markedAsDoneComment": marked_as_done_comment,
        "validatedAt": validated_at,
        "validatedBy": validated_by,
        "validationComment": validation_comment,
    }
    datetime_keys = {"startsAt", "endsAt", "deadline", "markedAsDoneAt", "validatedAt"}
    for key, value in expected.items():
        actual = data[key]

        if key in datetime_keys and isinstance(value, str) and isinstance(actual, str):
            assert actual.startswith(
                value
            ), f"data[{key!r}]: {actual!r} does not start with {value!r}"
        elif isinstance(value, dict) and isinstance(actual, dict):
            _assert_dict_subset(actual, value, path=f"data[{key!r}]")
        elif isinstance(value, list) and isinstance(actual, list):
            assert len(actual) == len(
                value
            ), f"data[{key!r}]: expected {len(value)} items, got {len(actual)}"
            for i, (act, exp) in enumerate(zip(actual, value, strict=True)):
                if isinstance(exp, dict) and isinstance(act, dict):
                    _assert_dict_subset(act, exp, path=f"data[{key!r}][{i}]")
                else:
                    assert act == exp, f"data[{key!r}][{i}]: {act!r} != {exp!r}"
        else:
            assert actual == value, f"data[{key!r}]: {actual!r} != {value!r}"


def assert_helper_shape(helper: dict, *, member_id: int) -> None:
    assert helper.keys() == HELPER_KEYS
    assert helper["member"].keys() == MEMBER_PUBLIC_INFO_KEYS
    assert helper["member"]["id"] == member_id
    assert isinstance(helper["signedUpAt"], str)


def assert_captain_shape(captain: dict, *, member_id: int) -> None:
    assert captain.keys() == HELPER_KEYS
    assert captain["member"].keys() == MEMBER_PUBLIC_INFO_KEYS
    assert captain["member"]["id"] == member_id
    assert isinstance(captain["signedUpAt"], str)
