"""
Keycloak authentication components.
"""
import logging
from typing import Tuple

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakInvalidTokenError
from pydantic import BaseModel

from ycc_hull.config import CONFIG
from ycc_hull.error import raise_401

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_AUTHENTICATION_FAILED = (
    "Missing or invalid token. Please log in. If you are logged in, "
    "then please log out and log in again."
)
_INACTIVE_USER = "Inactive user. Please contact the club."
_INACTIVE_MEMBER = "Inactive member. Please contact the club."

_YCC_ADMIN_ROLE = "ycc-admin"
_YCC_ACTIVE_MEMBER_ROLE = "ycc-member-active"
_YCC_COMMITTEE_MEMBER_ROLE = "ycc-member-committee"


class AuthInfo(BaseModel):
    """
    Authentication info.
    """

    # {
    #   "sub": "f1d54a64-2f67-4a49-860e-6d74cfa1e319",
    #   "email_verified": false,
    #   "name": "Lajos",
    #   "preferred_username": "lajos",
    #   "given_name": "Lajos",
    #   "family_name": ""
    # }
    user_info: dict
    # {
    #   "exp": 1677017737,
    #   "iat": 1677017437,
    #   "auth_time": 1677015164,
    #   "jti": "536b6610-d1e2-4744-8452-22c64a804baa",
    #   "iss": "http://localhost:10301/realms/Demo",
    #   "aud": "account",
    #   "sub": "f1d54a64-2f67-4a49-860e-6d74cfa1e319",
    #   "typ": "Bearer",
    #   "azp": "frontend",
    #   "nonce": "22a5f02b-dcda-4a41-b354-8f7903c1f1aa",
    #   "session_state": "86c1e8f9-8170-4357-8415-abe55af37aff",
    #   "name": "Lajos",
    #   "given_name": "Lajos",
    #   "family_name": "",
    #   "preferred_username": "lajos",
    #   "email_verified": false,
    #   "acr": "0",
    #   "allowed-origins": [
    #     "http://localhost:10300"
    #   ],
    #   "realm_access": {
    #     "roles": [
    #       "offline_access",
    #       "admin",
    #       "default-roles-demo",
    #       "uma_authorization",
    #       "demo"
    #     ]
    #   },
    #   "resource_access": {
    #     "account": {
    #       "roles": [
    #         "manage-account",
    #         "manage-account-links",
    #         "view-profile"
    #       ]
    #     }
    #   },
    #   "scope": "openid profile email",
    #   "sid": "86c1e8f9-8170-4357-8415-abe55af37aff",
    #   "client_id": "frontend",
    #   "username": "lajos",
    #   "active": true
    # }
    token_info: dict

    @property
    def user_name(self) -> str:
        return self.user_info["preferred_username"]

    @property
    def roles(self) -> Tuple[str]:
        return tuple(self.user_info["roles"])  # type: ignore

    @property
    def active_member(self) -> bool:
        return _YCC_ACTIVE_MEMBER_ROLE in self.roles

    @property
    def admin(self) -> bool:
        return _YCC_ADMIN_ROLE in self.roles

    @property
    def committee_member(self) -> bool:
        return _YCC_COMMITTEE_MEMBER_ROLE in self.roles

    class Config:
        """
        Immutable config.
        """

        allow_mutation = False


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
    server_url=CONFIG.keycloak_server,
    realm_name=CONFIG.keycloak_realm,
    client_id=CONFIG.keycloak_client,
    client_secret_key=CONFIG.keycloak_client_secret,
)
oauth2_scheme = init_oauth2_scheme()


async def auth(token: str = Depends(oauth2_scheme)) -> AuthInfo:
    """
    Authentication dependency.

    Args:
        token (str): OAuth 2 scheme bearer

    Raises:
        HTTPException: 401 Unauthorized

    Returns:
        AuthInfo: authentication info
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
            raise raise_401(_INACTIVE_USER)

        info = AuthInfo(user_info=user_info, token_info=token_info)
        logger.debug("Authentication succeeded: %s", info)

        if not info.active_member:
            logger.info("Inactive member: %s, roles: %s", info.user_name, info.roles)
            raise raise_401(_INACTIVE_MEMBER)

        logger.info(
            "Active member: %s, roles: %s",
            info.user_name,
            info.roles,
        )
        return info
    except (KeycloakAuthenticationError, KeycloakInvalidTokenError) as exc:
        logger.warning("Authentication failed: %s: %s", exc.__class__.__qualname__, exc)
        raise raise_401(_AUTHENTICATION_FAILED)  # pylint: disable=raise-missing-from
