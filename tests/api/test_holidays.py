"""Holidays API tests."""

from tests.api.conftest import client
from tests.main_test import FakeAuth


def test_holidays_get() -> None:
    FakeAuth.set_member()
    response = client.get("/api/v1/holidays")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 335
    dates = [h["date"] for h in data]
    assert dates == sorted(dates)
    assert data[0] == {"date": "2003-04-18", "label": "Good Friday"}
    assert data[-1] == {"date": "2049-12-31", "label": "New Year's Eve"}
