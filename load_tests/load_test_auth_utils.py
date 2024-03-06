"""
Authentication utilities for load tests.
"""

import requests

from load_tests.load_test_config import AUTH_CLIENT_ID, AUTH_REALM, AUTH_URL


def create_auth_header(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def get_access_token(user: str) -> str:
    response = requests.post(
        f"{AUTH_URL}/realms/{AUTH_REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": AUTH_CLIENT_ID,
            "username": user,
            "password": user,
            "scope": "openid profile email",
        },
        timeout=30,
    )
    assert response.status_code == 200, response

    return response.json()["access_token"]


def get_user_id(access_token: str) -> int:
    response = requests.post(
        f"{AUTH_URL}/realms/{AUTH_REALM}/protocol/openid-connect/userinfo",
        headers=create_auth_header(access_token),
        timeout=30,
    )
    assert response.status_code == 200, response

    # E.g., f:a9b693ac-d9aa-43c7-8b68-b3bb7d30cc8e:1
    return int(response.json()["sub"].split(":")[2])
