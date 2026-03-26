"""Global test configuration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def _no_smtp() -> Generator[None, None, None]:
    """Prevent real SMTP connections in tests."""
    mock = MagicMock()
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=False)
    mock.send_message = AsyncMock()
    mock.send_messages = AsyncMock()

    with patch(
        "ycc_hull.controllers.notifications.helpers_notifications_controller.SmtpConnection",
        return_value=mock,
    ):
        yield
