from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.mock_utils import patch_notifications


@pytest.fixture(scope="session", autouse=True)
def _no_smtp() -> Generator[None, None, None]:
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


@pytest.fixture
def mock_send_message() -> Generator[AsyncMock, None, None]:
    with patch_notifications() as send:
        yield send
