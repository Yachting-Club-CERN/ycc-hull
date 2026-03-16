"""SMTP connection and email sending."""

import logging
from email.message import EmailMessage
from types import TracebackType
from typing import Self

import aiosmtplib

from ycc_hull.config import CONFIG, EmailConfig
from ycc_hull.utils import full_type_name


class SmtpConnection:
    """Context manager for an SMTP connection."""

    def __init__(self, config: EmailConfig | None = None) -> None:
        """Initialise the SMTP connection context manager."""
        config_to_use = config or CONFIG.email
        if config_to_use is None:
            msg = "Email configuration is not set"
            raise ValueError(msg)

        self._logger = logging.getLogger(full_type_name(self.__class__))
        self._config = config_to_use
        self._smtp: aiosmtplib.SMTP | None = None

    async def __aenter__(self) -> Self:
        self._logger.info(
            "Connecting to SMTP server %s:%s as username=%s, start TLS: %s",
            self._config.smtp_host,
            self._config.smtp_port,
            self._config.smtp_username,
            self._config.smtp_start_tls,
        )

        self._smtp = aiosmtplib.SMTP(
            hostname=self._config.smtp_host,
            port=self._config.smtp_port,
            start_tls=self._config.smtp_start_tls,
            username=self._config.smtp_username,
            password=self._config.smtp_password,
        )
        await self._smtp.connect()

        self._logger.info("Connected to SMTP server")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        self._logger.info("Closing SMTP connection")

        if exc_type is not None:
            self._logger.exception(
                "Closing SMTP connection due to exception", exc_info=exc_value
            )

        if self._smtp:
            await self._smtp.quit()
            self._logger.info("SMTP connection was closed")
        else:
            self._logger.warning("SMTP connection was not established")

        # Propagate exception
        return False

    async def send_message(self, message: EmailMessage) -> None:
        """Send an email."""
        if not self._smtp:
            msg = "SMTP connection is not established"
            raise RuntimeError(msg)

        subject = f"{message['Subject']} - {CONFIG.ycc_app.name}"
        del message["Subject"]
        message["Subject"] = subject

        if self._config.content_header:
            # Add the header after <body> if present, otherwise at the beginning
            content = message.get_content()
            body_tag = "<body>"
            index = content.find(body_tag)

            if index != -1:
                offset = len(body_tag)
                content = (
                    f"{content[: index + offset]}\n"
                    f"{self._config.content_header}\n"
                    "<p>\n"
                    f"{content[index + offset :]}"
                )
            else:
                content = f"{self._config.content_header}\n\n{content}"

            message.set_content(
                content,
                subtype="html",
            )

        self._logger.info(
            "Sending email (Subject: %s, To: %s, Cc: %s, Bcc: %s, Reply-To: %s, "
            "content length: %d)",
            message["Subject"],
            message["To"],
            message["Cc"],
            message["Bcc"],
            message["Reply-To"],
            len(message.get_content()),
        )

        await self._smtp.send_message(message)

    async def send_messages(self, messages: list[EmailMessage]) -> None:
        """Send multiple emails."""
        for message in messages:
            await self.send_message(message)
