"""Scheduler tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

_MODULE = "ycc_hull.scheduler"


# ==============================================================================
# _parse_trigger
# ==============================================================================


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        (None, None),
        ("", None),
        (
            "cron:4 9 * * *",
            "cron[month='*', day='*', day_of_week='*', hour='9', minute='4']",
        ),
        (
            "cron:*/15 * * * *",
            "cron[month='*', day='*', day_of_week='*', hour='*', minute='*/15']",
        ),
        (
            "cron:0 8 * * 1-5",
            "cron[month='*', day='*', day_of_week='1-5', hour='8', minute='0']",
        ),
        ("interval-seconds:120", "interval[0:02:00]"),
        ("interval-seconds:1", "interval[0:00:01]"),
    ],
)
@patch(f"{_MODULE}.CONFIG")
def test_parse_trigger(
    _mock_config: MagicMock,  # noqa: PT019
    spec: str | None,
    expected: str | None,
) -> None:
    from ycc_hull.scheduler import _parse_trigger

    result = _parse_trigger(spec)
    if expected is None:
        assert result is None
    else:
        assert str(result) == expected


@pytest.mark.parametrize(
    ("spec", "error_type", "match"),
    [
        ("bogus:value", ValueError, r"^Unsupported trigger type: bogus$"),
        ("no-colon", ValueError, "not enough values to unpack"),
        ("interval-seconds:abc", ValueError, "invalid literal"),
        ("cron:bad", ValueError, "Wrong number of fields"),
    ],
)
@patch(f"{_MODULE}.CONFIG")
def test_parse_trigger_invalid(
    _mock_config: MagicMock,  # noqa: PT019
    spec: str,
    error_type: type,
    match: str,
) -> None:
    from ycc_hull.scheduler import _parse_trigger

    with pytest.raises(error_type, match=match):
        _parse_trigger(spec)


# ==============================================================================
# init_scheduler
# ==============================================================================


@pytest.mark.parametrize(
    ("trigger_spec", "expected_trigger"),
    [
        ("interval-seconds:60", "interval[0:01:00]"),
        (
            "cron:30 8 * * *",
            "cron[month='*', day='*', day_of_week='*', hour='8', minute='30']",
        ),
    ],
)
@patch(f"{_MODULE}.CONFIG")
def test_init_scheduler_with_trigger(
    mock_config: MagicMock,
    trigger_spec: str,
    expected_trigger: str,
) -> None:
    mock_config.notifications.daily_notifications_trigger = trigger_spec

    from ycc_hull.scheduler import init_scheduler

    app = MagicMock()
    scheduler = init_scheduler(app)

    assert isinstance(scheduler, AsyncIOScheduler)
    jobs = scheduler.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].name == "init_scheduler.<locals>.send_daily_helper_task_reminders"
    assert str(jobs[0].trigger) == expected_trigger


@patch(f"{_MODULE}.CONFIG")
def test_init_scheduler_disabled(mock_config: MagicMock) -> None:
    mock_config.notifications.daily_notifications_trigger = None

    from ycc_hull.scheduler import init_scheduler

    app = MagicMock()
    scheduler = init_scheduler(app)

    assert isinstance(scheduler, AsyncIOScheduler)
    assert len(scheduler.get_jobs()) == 0


@patch(f"{_MODULE}.CONFIG")
@pytest.mark.anyio
async def test_scheduled_job_calls_send_daily_reminders(mock_config: MagicMock) -> None:
    mock_config.notifications.daily_notifications_trigger = "interval-seconds:60"

    from ycc_hull.scheduler import init_scheduler

    app = MagicMock()
    mock_controller = AsyncMock()
    app.state.controllers.helpers_controller = mock_controller

    scheduler = init_scheduler(app)
    job = scheduler.get_jobs()[0]

    # Execute the job function directly
    await job.func()

    mock_controller.send_daily_reminders.assert_awaited_once()


@patch(f"{_MODULE}.CONFIG")
@pytest.mark.anyio
async def test_scheduled_job_raises_on_failure(mock_config: MagicMock) -> None:
    mock_config.notifications.daily_notifications_trigger = "interval-seconds:60"

    from ycc_hull.scheduler import init_scheduler

    app = MagicMock()
    mock_controller = AsyncMock()
    mock_controller.send_daily_reminders.side_effect = RuntimeError("boom")
    app.state.controllers.helpers_controller = mock_controller

    scheduler = init_scheduler(app)
    job = scheduler.get_jobs()[0]

    with pytest.raises(RuntimeError, match=r"^boom$"):
        await job.func()
