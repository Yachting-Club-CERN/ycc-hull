"""Auth module tests."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakInvalidTokenError

_MODULE = "ycc_hull.auth"


# ==============================================================================
# _create_user
# ==============================================================================


def _sample_user_info() -> dict:
    return {
        "sub": "f:034bfedc-ed3d-4169-be68-9fd337eddff2:292",
        "email_verified": False,
        "roles": ["ycc-member-active", "ycc-helpers-app-admin"],
        "name": "Michele Huff",
        "groups": ["ycc-members-all-past-and-present"],
        "preferred_username": "MHUFF",
        "given_name": "Michele",
        "family_name": "Huff",
        "email": "michele.huff@mailinator.com",
    }


def _sample_token_info() -> dict:
    return {
        "sub": "f:034bfedc-ed3d-4169-be68-9fd337eddff2:292",
        "preferred_username": "MHUFF",
        "given_name": "Michele",
        "family_name": "Huff",
        "email": "michele.huff@mailinator.com",
        "realm_access": {
            "roles": ["ycc-member-active", "ycc-helpers-app-admin"],
        },
        "active": True,
    }


def test_create_user_from_user_info() -> None:
    from ycc_hull.auth import _create_user

    user = _create_user(_sample_user_info(), _sample_token_info())

    assert user.member_id == 292
    assert user.username == "MHUFF"
    assert user.email == "michele.huff@mailinator.com"
    assert user.first_name == "Michele"
    assert user.last_name == "Huff"
    assert user.groups == ("ycc-members-all-past-and-present",)
    assert user.roles == ("ycc-member-active", "ycc-helpers-app-admin")
    assert user.active_member is True
    assert user.helpers_app_admin is True


def test_create_user_falls_back_to_token_info() -> None:
    from ycc_hull.auth import _create_user

    # Minimal user_info - forces fallback to token_info for most fields
    user_info = {"sub": "f:id:42"}
    token_info = _sample_token_info()
    token_info["sub"] = "f:id:42"
    token_info["username"] = "TOKENUSER"

    user = _create_user(user_info, token_info)

    assert user.member_id == 42
    assert user.username == "TOKENUSER"
    assert user.email == "michele.huff@mailinator.com"
    assert user.first_name == "Michele"
    assert user.last_name == "Huff"
    assert user.groups == ()
    assert user.roles == ("ycc-member-active", "ycc-helpers-app-admin")


def test_create_user_roles_from_realm_access() -> None:
    from ycc_hull.auth import _create_user

    # No roles in user_info, should fall back to token_info.realm_access.roles
    user_info = {
        "sub": "f:id:5",
        "preferred_username": "U",
        "given_name": "F",
        "family_name": "L",
        "email": "u@example.com",
    }
    token_info = {
        "sub": "f:id:5",
        "realm_access": {"roles": ["ycc-admin"]},
        "active": True,
    }

    user = _create_user(user_info, token_info)

    assert user.roles == ("ycc-admin",)


# ==============================================================================
# auth
# ==============================================================================


@patch(f"{_MODULE}._KEYCLOAK")
@pytest.mark.anyio
async def test_auth_success(mock_keycloak: MagicMock) -> None:
    from ycc_hull.auth import auth

    mock_keycloak.userinfo.return_value = _sample_user_info()
    mock_keycloak.introspect.return_value = _sample_token_info()

    user = await auth(token="valid-token")  # noqa: S106

    assert user.member_id == 292
    assert user.username == "MHUFF"
    assert user.active_member is True
    mock_keycloak.userinfo.assert_called_once_with("valid-token")
    mock_keycloak.introspect.assert_called_once_with("valid-token")


@patch(f"{_MODULE}._KEYCLOAK")
@pytest.mark.anyio
async def test_auth_inactive_token(mock_keycloak: MagicMock) -> None:
    from ycc_hull.auth import auth

    mock_keycloak.userinfo.return_value = _sample_user_info()
    token_info = _sample_token_info()
    token_info["active"] = False
    mock_keycloak.introspect.return_value = token_info

    with pytest.raises(HTTPException) as exc_info:
        await auth(token="inactive-token")  # noqa: S106

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Inactive user. Please contact the club."


@patch(f"{_MODULE}._KEYCLOAK")
@pytest.mark.anyio
async def test_auth_inactive_member(mock_keycloak: MagicMock) -> None:
    from ycc_hull.auth import auth

    user_info = _sample_user_info()
    user_info["roles"] = []  # no active member role
    mock_keycloak.userinfo.return_value = user_info

    token_info = _sample_token_info()
    token_info["realm_access"]["roles"] = []
    mock_keycloak.introspect.return_value = token_info

    with pytest.raises(HTTPException) as exc_info:
        await auth(token="member-token")  # noqa: S106

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Inactive member. Please contact the club."


@patch(f"{_MODULE}._KEYCLOAK")
@pytest.mark.anyio
async def test_auth_keycloak_authentication_error(mock_keycloak: MagicMock) -> None:
    from ycc_hull.auth import auth

    mock_keycloak.userinfo.side_effect = KeycloakAuthenticationError()

    with pytest.raises(HTTPException) as exc_info:
        await auth(token="bad-token")  # noqa: S106

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "Missing or invalid token. Please log in. If you are logged in, "
        "then please log out and log in again."
    )


@patch(f"{_MODULE}._KEYCLOAK")
@pytest.mark.anyio
async def test_auth_keycloak_invalid_token_error(mock_keycloak: MagicMock) -> None:
    from ycc_hull.auth import auth

    mock_keycloak.userinfo.side_effect = KeycloakInvalidTokenError()

    with pytest.raises(HTTPException) as exc_info:
        await auth(token="expired-token")  # noqa: S106

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "Missing or invalid token. Please log in. If you are logged in, "
        "then please log out and log in again."
    )
