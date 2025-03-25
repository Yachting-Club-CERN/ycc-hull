"""
Application configuration.
"""

import json
import os
from enum import Enum
from logging import Logger

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

    from_email: str
    content_header: str | None = Field(
        default=None, json_schema_extra={"sanitise": False}
    )
    smtp_host: str
    smtp_port: int
    smtp_start_tls: bool
    smtp_username: str | None = None
    smtp_password: str | None = None


class KeycloakConfig(CamelisedBaseModel):
    """
    Keycloak configuration.
    """

    server_url: str
    realm: str
    client: str
    client_secret: str
    swagger_client: str | None = None


class NotificationsConfig(CamelisedBaseModel):
    """
    Notifications configuration.
    """

    daily_notifications_trigger: str | None = Field(
        description=(
            "Trigger for daily notifications. For production it could be e.g., `cron: 4 9 * * *` for testing you can also use `interval-seconds: 120`."
            "If None, notifications are disabled."
        )
    )


class YccAppConfig(CamelisedBaseModel):
    """
    YCC App configuration.
    """

    name: str
    base_url: str


class Config(CamelisedBaseModel):
    """
    Application configuration.
    """

    model_config = ConfigDict(frozen=True)

    environment: Environment
    database_url: str
    cors_origins: frozenset[str]
    email: EmailConfig | None = None
    keycloak: KeycloakConfig
    notifications: NotificationsConfig
    uvicorn_port: int
    ycc_app: YccAppConfig

    @property
    def local(self) -> bool:
        return self.environment == Environment.LOCAL

    @property
    def api_docs_enabled(self) -> bool:
        return self.environment in (Environment.LOCAL, Environment.DEVELOPMENT)

    def emails_enabled(self, logger: Logger) -> bool:
        if self.email:
            return True

        logger.info("Email configuration is not set, skipping notifications")
        return False


CONFIG: Config


if os.path.isfile(CONFIG_FILE):
    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        _config_data = json.load(file)
        CONFIG = Config(**_config_data)
else:
    raise AssertionError(f"Missing configuration file: {CONFIG_FILE}")
