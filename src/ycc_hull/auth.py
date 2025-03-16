"""
Keycloak authentication components.
"""

import logging

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakInvalidTokenError

from ycc_hull.api.errors import create_http_exception_401
from ycc_hull.config import CONFIG
from ycc_hull.models.user import User
from ycc_hull.utils import full_type_name

_logger = logging.getLogger(__name__)

_AUTHENTICATION_FAILED = (
    "Missing or invalid token. Please log in. If you are logged in, "
    "then please log out and log in again."
)
_INACTIVE_USER = "Inactive user. Please contact the club."
_INACTIVE_MEMBER = "Inactive member. Please contact the club."


_KEYCLOAK = KeycloakOpenID(
    server_url=CONFIG.keycloak_server_url,
    realm_name=CONFIG.keycloak_realm,
    client_id=CONFIG.keycloak_client,
    client_secret_key=CONFIG.keycloak_client_secret,
)


# Programmatic access to the token endpoint: _KEYCLOAK.well_known()["token_endpoint"]
TOKEN_ENDPOINT = f"{CONFIG.keycloak_server_url}/realms/{CONFIG.keycloak_realm}/protocol/openid-connect/token"
_logger.info("Initialising OAuth 2 scheme with token endpoint: %s", TOKEN_ENDPOINT)
_OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl=TOKEN_ENDPOINT)


def _create_user(user_info: dict, token_info: dict) -> User:
    """
    Creates a user.

    User info looks like this:

    ```
    {
        'sub': 'f:034bfedc-ed3d-4169-be68-9fd337eddff2:1',
        'email_verified': False,
        'roles': ['ycc-member-active', 'offline_access', 'ycc-helpers-app-admin', 'uma_authorization'],
        'name': 'Michele Huff',
        'groups': ['ycc-members-all-past-and-present'],
        'preferred_username': 'MHUFF',
        'given_name': 'Michele',
        'family_name': 'Huff',
        'email': 'Michele.Huff@mailinator.com'
    }
    ```

    Token info looks like this:

    ```
    {
        'exp': 1681553258,
        'iat': 1681549658,
        'jti': 'c4e866ab-3ec0-4c35-a8ea-a2fc789204ad',
        'iss': 'http://localhost:8080/realms/YCC-LOCAL',
        'aud': 'account',
        'sub': 'f:034bfedc-ed3d-4169-be68-9fd337eddff2:1',
        'typ': 'Bearer',
        'azp': 'ycc-hull-local-swagger',
        'session_state': '0b1bdf08-7d0d-4a50-9804-9faffb6daa88',
        'name': 'Michele Huff',
        'given_name': 'Michele',
        'family_name': 'Huff',
        'preferred_username': 'MHUFF',
        'email': 'Michele.Huff@mailinator.com',
        'email_verified': False,
        'acr': '1',
        'allowed-origins': ['http://localhost:8000'],
        'realm_access': {'roles': ['ycc-member-active', 'offline_access', 'ycc-helpers-app-admin', 'uma_authorization']},
        'resource_access': {'account': {'roles': ['manage-account', 'manage-account-links', 'view-profile']}},
        'scope': 'openid profile ycc-client-groups-and-roles email',
        'sid': '0b1bdf08-7d0d-4a50-9804-9faffb6daa88',
        'client_id': 'ycc-hull-local-swagger',
        'username': 'MHUFF',
        'active': True
    }
    ```

    Args:
        user_info (dict): user info
        token_info (dict): token info

    Returns:
        User: user object
    """

    return User(
        # 292 is YCC DB ID from sub 'f:a9b693ac-d9aa-43c7-8b68-b3bb7d30cc8e:292'
        member_id=int(user_info.get("sub", token_info.get("sub")).split(":")[-1]),
        username=user_info.get(
            "preferred_username",
            token_info.get("username", token_info.get("preferred_username")),
        ),
        groups=tuple(user_info.get("groups", [])),
        roles=tuple(
            user_info.get("roles", token_info.get("realm_access", {}).get("roles", []))
        ),
    )


async def auth(token: str = Depends(_OAUTH2_SCHEME)) -> User:
    """
    Authentication dependency.

    Args:
        token (str): OAuth 2 scheme bearer

    Raises:
        HTTPException: 401 Unauthorized

    Returns:
        User: user object
    """
    _logger.debug("Authenticating...")
    try:
        _logger.debug("Token: %s", token)

        user_info = _KEYCLOAK.userinfo(token)  # cspell:disable-line
        _logger.debug("User info: %s", user_info)
        token_info = _KEYCLOAK.introspect(token)
        _logger.debug("Token info: %s", token_info)

        if not token_info["active"]:
            _logger.warning("Authentication failed")
            raise create_http_exception_401(_INACTIVE_USER)

        user = _create_user(user_info=user_info, token_info=token_info)
        _logger.debug("Authentication succeeded: %s", user)

        if not user.active_member:
            _logger.info("Inactive member: %s, roles: %s", user.username, user.roles)
            raise create_http_exception_401(_INACTIVE_MEMBER)

        _logger.info(
            "Active member: %s (%d), groups: %s, roles: %s",
            user.username,
            user.member_id,
            user.groups,
            user.roles,
        )
        return user
    except (KeycloakAuthenticationError, KeycloakInvalidTokenError) as exc:
        _logger.warning(
            "Authentication failed: %s: %s", full_type_name(exc.__class__), exc
        )
        raise create_http_exception_401(  # pylint: disable=raise-missing-from
            _AUTHENTICATION_FAILED
        )
