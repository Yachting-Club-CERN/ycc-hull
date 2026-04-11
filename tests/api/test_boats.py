from tests.api.conftest import client
from tests.test_main import FakeAuth


def test_boats_get() -> None:
    FakeAuth.set_member()
    response = client.get("/api/v1/boats")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 46
    assert data[0] == {
        "id": 1,
        "name": "Charm",
        "type": "Laser II",
        "licence": "D",
        "class": "DGY",
        "capacity": 2,
        "tablePosition": None,
    }
    assert data[-1] == {
        "id": 27,
        "name": "Tools&Karcher ABP",
        "type": "Toolbox",
        "licence": "ALL",
        "class": "TOOL",
        "capacity": None,
        "tablePosition": 1000,
    }
