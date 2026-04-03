from tests.api.conftest import client
from tests.test_main import FakeAuth


def test_licence_infos_get() -> None:
    FakeAuth.set_member()
    response = client.get("/api/v1/licence-infos")

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 22
    codes = [d["licence"] for d in data]
    assert codes == sorted(codes)
    assert data[0] == {"id": 4, "licence": "C", "description": "SL16"}
    assert data[-1] == {"id": 5, "licence": "Y", "description": "Yngling"}
