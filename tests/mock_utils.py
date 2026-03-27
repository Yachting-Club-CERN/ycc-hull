"""Shared mock factories for tests."""

from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch


def make_mock_smtp() -> MagicMock:
    """Create a mock SmtpConnection that captures sent EmailMessage objects."""
    mock_smtp = MagicMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.__aenter__ = AsyncMock(return_value=mock_smtp)
    mock_smtp.__aexit__ = AsyncMock(return_value=False)
    return mock_smtp


def make_mock_config(
    *,
    emails_enabled: bool = True,
    from_email: str = "noreply@test.ycc.test",
    app_name: str = "YCC Test",
    base_url: str = "https://app.ycc.test",
    content_header: str | None = None,
) -> MagicMock:
    """Create a mock CONFIG object for notification tests."""
    cfg = MagicMock()
    cfg.emails_enabled.return_value = emails_enabled
    if emails_enabled:
        cfg.email.from_email = from_email
        cfg.email.content_header = content_header
    else:
        cfg.email = None
    cfg.ycc_app.name = app_name
    cfg.ycc_app.base_url = base_url
    return cfg


# ==============================================================================
# Patch helpers for notification tests
# ==============================================================================

_HELPERS_MODULE = "ycc_hull.controllers.helpers_controller"
_NOTIFICATIONS_MODULE = (
    "ycc_hull.controllers.notifications.helpers_notifications_controller"
)
_BUILDER_MODULE = "ycc_hull.controllers.notifications.email_message_builder"

_NOTIFICATIONS_CONFIG = f"{_NOTIFICATIONS_MODULE}.CONFIG"
_NOTIFICATIONS_SMTP = f"{_NOTIFICATIONS_MODULE}.SmtpConnection"


def _make_notifications_mocks(
    *,
    emails_enabled: bool = True,
) -> tuple[MagicMock, MagicMock, AsyncMock]:
    """Create the (config, smtp_class, send_message) triple for notification tests."""
    cfg = make_mock_config(emails_enabled=emails_enabled)
    smtp_instance = make_mock_smtp()
    send = smtp_instance.send_message
    smtp_class = MagicMock(return_value=smtp_instance)
    return cfg, smtp_class, send


@contextmanager
def patch_notifications(
    *,
    emails_enabled: bool = True,
) -> Generator[AsyncMock, None, None]:
    """Patch CONFIG and SmtpConnection for notification tests.

    Yields the ``send_message`` AsyncMock for assertions.
    """
    cfg, smtp_class, send = _make_notifications_mocks(emails_enabled=emails_enabled)
    with patch(_NOTIFICATIONS_CONFIG, cfg), patch(_NOTIFICATIONS_SMTP, smtp_class):
        yield send


@contextmanager
def patch_notifications_with_sleep() -> (
    Generator[tuple[AsyncMock, AsyncMock], None, None]
):
    """Patch CONFIG, SmtpConnection, and asyncio.sleep for reminder tests.

    Yields ``(send_message, mock_sleep)`` for assertions.
    """
    with (
        patch_notifications() as send,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        yield send, mock_sleep


@contextmanager
def patch_reminders(
    *,
    now: datetime,
    emails_enabled: bool = True,
    from_email: str = "noreply@test.ycc.test",
    app_name: str = "YCC Test",
) -> Generator[MagicMock, None, None]:
    """Patch all modules involved in send_daily_reminders.

    Patches CONFIG in helpers_controller, notifications_controller, and
    email_message_builder, plus get_now, SmtpConnection, and asyncio.sleep.

    Yields the mock SMTP instance (use ``smtp.send_message.call_args_list` to
    inspect sent emails).
    """
    cfg = make_mock_config(
        emails_enabled=emails_enabled,
        from_email=from_email,
        app_name=app_name,
    )
    mock_smtp = make_mock_smtp()
    smtp_class = MagicMock(return_value=mock_smtp)

    with (
        patch(f"{_HELPERS_MODULE}.CONFIG", cfg),
        patch(f"{_HELPERS_MODULE}.get_now", return_value=now),
        patch(_NOTIFICATIONS_CONFIG, cfg),
        patch(_NOTIFICATIONS_SMTP, smtp_class),
        patch(f"{_NOTIFICATIONS_MODULE}.asyncio.sleep", new_callable=AsyncMock),
        patch(f"{_BUILDER_MODULE}.CONFIG", cfg),
    ):
        yield mock_smtp
