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

logger = logging.getLogger(__name__)

_AUTHENTICATION_FAILED = (
    "Missing or invalid token. Please log in. If you are logged in, "
    "then please log out and log in again."
)
_INACTIVE_USER = "Inactive user. Please contact the club."
_INACTIVE_MEMBER = "Inactive member. Please contact the club."


def _create_user(user_info: dict, token_info: dict) -> User:
    # User info:
    #
    # {
    # 'sub': 'f:034bfedc-ed3d-4169-be68-9fd337eddff2:1',
    # 'email_verified': False,
    # 'roles': ['ycc-member-active', 'offline_access', 'ycc-helpers-app-admin', 'uma_authorization'],
    # 'name': 'Michele Huff',
    # 'groups': ['ycc-members-all-past-and-present'],
    # 'preferred_username': 'MHUFF',
    # 'given_name': 'Michele',
    # 'family_name': 'Huff',
    # 'email': 'Michele.Huff@mailinator.com'}

    # Token info:
    #
    # {
    # 'exp': 1681553258,
    # 'iat': 1681549658,
    # 'jti': 'c4e866ab-3ec0-4c35-a8ea-a2fc789204ad',
    # 'iss': 'http://localhost:8080/realms/YCC-LOCAL',
    # 'aud': 'account',
    # 'sub': 'f:034bfedc-ed3d-4169-be68-9fd337eddff2:1',
    # 'typ': 'Bearer',
    # 'azp': 'ycc-hull-local-swagger',
    # 'session_state': '0b1bdf08-7d0d-4a50-9804-9faffb6daa88',
    # 'name': 'Michele Huff',
    # 'given_name': 'Michele',
    # 'family_name': 'Huff',
    # 'preferred_username': 'MHUFF',
    # 'email': 'Michele.Huff@mailinator.com',
    # 'email_verified': False,
    # 'acr': '1',
    # 'allowed-origins': ['http://localhost:8000'],
    # 'realm_access': {'roles': ['ycc-member-active', 'offline_access', 'ycc-helpers-app-admin', 'uma_authorization']},
    # 'resource_access': {'account': {'roles': ['manage-account', 'manage-account-links', 'view-profile']}},
    # 'scope': 'openid profile ycc-client-groups-and-roles email',
    # 'sid': '0b1bdf08-7d0d-4a50-9804-9faffb6daa88',
    # 'client_id': 'ycc-hull-local-swagger',
    # 'username': 'MHUFF',
    # 'active': True
    # }

    return User(
        # 292 is YCC DB ID from sub 'f:a9b693ac-d9aa-43c7-8b68-b3bb7d30cc8e:292'
        member_id=int(user_info["sub"].split(":")[-1]),
        username=user_info["preferred_username"],
        groups=tuple(user_info.get("groups", [])),
        roles=tuple(user_info.get("roles", [])),
    )


def init_oauth2_scheme() -> OAuth2PasswordBearer:
    """
    Initialises OAuth 2 scheme.

    Returns:
        OAuth2PasswordBearer: bearer
    """
    token_endpoint = keycloak.well_known()["token_endpoint"]
    logger.info("Initialising OAuth 2 scheme with token endpoint: %s", token_endpoint)
    return OAuth2PasswordBearer(tokenUrl=token_endpoint)


keycloak = KeycloakOpenID(
    server_url=CONFIG.keycloak_server_url,
    realm_name=CONFIG.keycloak_realm,
    client_id=CONFIG.keycloak_client,
    client_secret_key=CONFIG.keycloak_client_secret,
)
oauth2_scheme = init_oauth2_scheme()


async def auth(token: str = Depends(oauth2_scheme)) -> User:
    """
    Authentication dependency.

    Args:
        token (str): OAuth 2 scheme bearer

    Raises:
        HTTPException: 401 Unauthorized

    Returns:
        User: user object
    """
    logger.debug("Authenticating...")
    try:
        logger.debug("Token: %s", token)

        user_info = keycloak.userinfo(token)  # cspell:disable-line
        logger.debug("User info: %s", user_info)
        token_info = keycloak.introspect(token)
        logger.debug("Token info: %s", token_info)

        if not token_info["active"]:
            logger.warning("Authentication failed")
            raise create_http_exception_401(_INACTIVE_USER)

        user = _create_user(user_info=user_info, token_info=token_info)
        logger.debug("Authentication succeeded: %s", user)

        if not user.active_member:
            logger.info("Inactive member: %s, roles: %s", user.username, user.roles)
            raise create_http_exception_401(_INACTIVE_MEMBER)

        logger.info(
            "Active member: %s (%d), groups: %s, roles: %s",
            user.username,
            user.member_id,
            user.groups,
            user.roles,
        )
        return user
    except (KeycloakAuthenticationError, KeycloakInvalidTokenError) as exc:
        logger.warning("Authentication failed: %s: %s", exc.__class__.__qualname__, exc)
        raise create_http_exception_401(  # pylint: disable=raise-missing-from
            _AUTHENTICATION_FAILED
        )
