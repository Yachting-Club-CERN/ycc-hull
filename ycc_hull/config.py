"""
Application configuration.
"""
import json
import os
from enum import Enum
from typing import FrozenSet, Optional

from ycc_hull.models.base import CamelisedBaseModel


CONFIG_FILE = "conf/config.json"
LOGGING_CONFIG_FILE = "conf/logging.conf"


class Environment(str, Enum):
    """
    Environment enumeration.
    """

    PRODUCTION = "PRODUCTION"
    TEST = "TEST"
    DEVELOPMENT = "DEVELOPMENT"
    LOCAL = "LOCAL"


class Config(CamelisedBaseModel):
    """
    Application configuration.
    """

    environment: Environment
    db_url: str
    cors_origins: FrozenSet[str]
    keycloak_server_url: str
    keycloak_realm: str
    keycloak_client: str
    keycloak_client_secret: str
    keycloak_swagger_client: Optional[str]
    uvicorn_port: int = 8000

    @property
    def is_local(self) -> bool:
        return self.environment == Environment.LOCAL

    class Config:
        """
        Immutable config.
        """

        allow_mutation = False


CONFIG: Config


if os.path.isfile(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        _config_data = json.load(file)
        CONFIG = Config(**_config_data)
else:
    raise AssertionError(f"Missing configuration file: {CONFIG_FILE}")
