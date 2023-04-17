"""
Application configuration.
"""
import json
import os
from enum import Enum
from typing import Optional

from ycc_hull.models.base import CamelisedBaseModelWithEntity

CONFIG_FILE = (
    "conf/config-dev.json"
    if os.path.exists("conf/config-dev.json")
    else "conf/config.json"
)

LOGGING_CONFIG_FILE = "conf/logging.conf"


class Environment(str, Enum):
    """
    Environment enumeration.
    """

    PRODUCTION = "PRODUCTION"
    TEST = "TEST"
    DEVELOPMENT = "DEVELOPMENT"
    LOCAL = "LOCAL"


class Config(CamelisedBaseModelWithEntity):
    """
    Application configuration.
    """

    environment: Environment
    database_url: str
    cors_origins: frozenset[str]
    keycloak_server_url: str
    keycloak_realm: str
    keycloak_client: str
    keycloak_client_secret: str
    keycloak_swagger_client: Optional[str]
    uvicorn_port: int

    @property
    def local(self) -> bool:
        return self.environment == Environment.LOCAL

    @property
    def api_docs_enabled(self) -> bool:
        return self.environment in (Environment.LOCAL, Environment.DEVELOPMENT)

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
