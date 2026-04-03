from test_data.generator_config import MEMBER_COUNT
from tests.api.conftest import client
from tests.main_test import FakeAuth
from ycc_hull.utils import get_now

CURRENT_YEAR = get_now().year


# ==============================================================================
# GET /api/v1/members
# ==============================================================================


def test_members_get_current_year() -> None:
    FakeAuth.set_member()
    response = client.get(f"/api/v1/members?year={CURRENT_YEAR}")

    assert response.status_code == 200
    data = response.json()

    assert len(data) > 200
    names = [(m["lastName"], m["firstName"]) for m in data]
    assert names == sorted(names)


def test_members_get_missing_year_returns_422() -> None:
    FakeAuth.set_member()
    response = client.get("/api/v1/members")
    assert response.status_code == 422


def test_members_get_past_year_forbidden_for_member() -> None:
    FakeAuth.set_member()
    response = client.get(f"/api/v1/members?year={CURRENT_YEAR - 1}")
    assert response.status_code == 403


def test_members_get_future_year_forbidden_for_member() -> None:
    FakeAuth.set_member()
    response = client.get(f"/api/v1/members?year={CURRENT_YEAR + 1}")
    assert response.status_code == 403


def test_members_get_past_year_allowed_for_admin() -> None:
    FakeAuth.set_admin()
    response = client.get(f"/api/v1/members?year={CURRENT_YEAR - 1}")
    assert response.status_code == 200
    assert len(response.json()) > 200


def test_members_get_past_year_allowed_for_committee() -> None:
    FakeAuth.set_committee_member()
    response = client.get(f"/api/v1/members?year={CURRENT_YEAR - 1}")
    assert response.status_code == 200
    assert len(response.json()) > 200


# ==============================================================================
# GET /api/v1/membership-types
# ==============================================================================


def test_membership_types_get() -> None:
    FakeAuth.set_member()
    response = client.get("/api/v1/membership-types")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 6
    descriptions = [mt["descriptionEn"] for mt in data]
    assert descriptions == sorted(descriptions)
    assert data[0] == {
        "id": 1,
        "name": "AS",
        "descriptionEn": "Active",
        "descriptionFr": "Active",
        "comments": "For all club activities.",
    }
    assert data[-1] == {
        "id": 5,
        "name": "T",
        "descriptionEn": "Temporary",
        "descriptionFr": "Temporaire",
        "comments": (
            "Only short-term visitors to CERN (less than 6\n"
            "months), for a period not exceeding 2 months.\n"
            "May not be temporary members for two consecutive seasons."
        ),
    }


# ==============================================================================
# GET /api/v1/users
# ==============================================================================


def test_users_get_as_admin() -> None:
    FakeAuth.set_admin()
    response = client.get("/api/v1/users")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == MEMBER_COUNT
    usernames = [u["username"] for u in data]
    assert usernames == sorted(usernames)


def test_users_get_forbidden_for_member() -> None:
    FakeAuth.set_member()
    response = client.get("/api/v1/users")
    assert response.status_code == 403
