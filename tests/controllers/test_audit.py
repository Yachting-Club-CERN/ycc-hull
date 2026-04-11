from datetime import UTC, date, datetime

import pytest

from tests.factories import make_user
from ycc_hull.controllers.audit import (
    _to_json_dict,
    _to_pretty_json,
    create_audit_entry,
)

# ==============================================================================
# _to_json_dict
# ==============================================================================


def test_to_json_dict_datetime() -> None:
    dt = datetime(2026, 3, 15, 10, 30, 0, tzinfo=UTC)
    result = _to_json_dict(dt)
    assert result == {"@type": "datetime", "value": "2026-03-15T10:30:00+00:00"}


def test_to_json_dict_date() -> None:
    d = date(2026, 3, 15)
    result = _to_json_dict(d)
    assert result == {"@type": "date", "value": "2026-03-15"}


def test_to_json_dict_pydantic_model() -> None:
    user = make_user()
    result = _to_json_dict(user)
    assert result == {
        "@type": "ycc_hull.models.user.User",
        "memberId": 1,
        "username": "testuser",
        "email": "test@example.com",
        "firstName": "Test",
        "lastName": "User",
        "groups": (),
        "roles": (),
    }


def test_to_json_dict_unsupported_type() -> None:
    with pytest.raises(TypeError, match=r"^Cannot serialize type: <class 'int'>$"):
        _to_json_dict(12345)


# ==============================================================================
# _to_pretty_json
# ==============================================================================


def test_to_pretty_json_with_date() -> None:
    data = {"when": date(2026, 1, 1)}
    result = _to_pretty_json(data)
    assert result == (
        '{\n  "when": {\n    "@type": "date",\n    "value": "2026-01-01"\n  }\n}'
    )


# ==============================================================================
# create_audit_entry
# ==============================================================================


def test_create_audit_entry_with_data() -> None:
    user = make_user()
    entry = create_audit_entry(user, "Test action", data={"key": "value"})

    assert entry.principal == "testuser"
    assert entry.description == "Test action"
    assert isinstance(entry.data, str)
    assert entry.data == '{\n  "key": "value"\n}'


def test_create_audit_entry_without_data() -> None:
    user = make_user()
    entry = create_audit_entry(user, "Test action")

    assert entry.principal == "testuser"
    assert entry.description == "Test action"
    assert entry.data is None
