"""
Application configuration.
"""

import json
import os
from enum import Enum

from pydantic import ConfigDict, Field

from ycc_hull.constants import CONFIG_FILE
from ycc_hull.models.base import CamelisedBaseModel


class Environment(str, Enum):
    """
    Environment enumeration.
    """

    PRODUCTION = "PRODUCTION"
    TEST = "TEST"
    DEVELOPMENT = "DEVELOPMENT"
    LOCAL = "LOCAL"


class EmailConfig(CamelisedBaseModel):
    """
    Email configuration.
    """

    from_name: str
    from_email: str
    subject_prefix: str | None
    content_header: str | None = Field(json_schema_extra={"sanitise": False})
    smtp_host: str
    smtp_port: int
    smtp_start_tls: bool
    smtp_username: str
    smtp_password: str


class Config(CamelisedBaseModel):
    """
    Application configuration.
    """

    model_config = ConfigDict(frozen=True)

    environment: Environment
    database_url: str
    cors_origins: frozenset[str]
    email: EmailConfig | None
    keycloak_server_url: str
    keycloak_realm: str
    keycloak_client: str
    keycloak_client_secret: str
    keycloak_swagger_client: str | None
    uvicorn_port: int
    ycc_app_base_url: str

    @property
    def local(self) -> bool:
        return self.environment == Environment.LOCAL

    @property
    def api_docs_enabled(self) -> bool:
        return self.environment in (Environment.LOCAL, Environment.DEVELOPMENT)


CONFIG: Config


if os.path.isfile(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        _config_data = json.load(file)
        CONFIG = Config(**_config_data)
else:
    raise AssertionError(f"Missing configuration file: {CONFIG_FILE}")
