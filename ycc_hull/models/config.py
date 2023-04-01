"""
Configuration classes.
"""
from enum import Enum
from typing import FrozenSet

from ycc_hull.models.base import CamelisedBaseModel


class Environment(str, Enum):
    """
    Environment enumeration.
    """

    PRODUCTION = "PRODUCTION"
    NEXT = "NEXT"
    DEV = "DEV"
    LOCAL = "LOCAL"


class Config(CamelisedBaseModel):
    """
    Application configuration.
    """

    environment: Environment
    db_url: str
    cors_origins: FrozenSet[str]
    keycloak_server: str
    keycloak_realm: str
    keycloak_client: str
    keycloak_client_secret: str
    uvicorn_port: int = 8000

    @property
    def is_local(self) -> bool:
        return self.environment == Environment.LOCAL

    class Config:
        """
        Immutable config.
        """

        allow_mutation = False
