"""
Scheduler for running recurring background jobs.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.base import BaseTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from ycc_hull.app_controllers import get_controllers
from ycc_hull.config import CONFIG
from ycc_hull.constants import TIME_ZONE_ID

_logger = logging.getLogger(__name__)


def _parse_trigger(trigger_str: str | None) -> BaseTrigger | None:
    if not trigger_str:
        return None

    trigger_type, trigger_value = trigger_str.split(":", 1)

    if trigger_type == "cron":
        return CronTrigger.from_crontab(trigger_value)
    if trigger_type == "interval-seconds":
        return IntervalTrigger(seconds=int(trigger_value))

    raise ValueError(f"Unsupported trigger type: {trigger_type}")


def init_scheduler(app: FastAPI) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=TIME_ZONE_ID)

    trigger = _parse_trigger(CONFIG.notifications.daily_notifications_trigger)

    if trigger:
        _logger.info("Using schedule %s for daily helper task reminders", trigger)

        @scheduler.scheduled_job(trigger=trigger)
        async def send_daily_helper_task_reminders() -> None:
            task_name = send_daily_helper_task_reminders.__name__

            _logger.info("Starting scheduled task: %s", task_name)

            try:
                await get_controllers(app).helpers_controller.send_daily_reminders()

                _logger.info("Scheduled task finished: %s", task_name)
            except Exception:
                _logger.exception("Scheduled task failed: %s", task_name)
                raise

    else:
        _logger.info("Daily helper task reminders are disabled")

    return scheduler
