import asyncio
import copy
import logging
from collections import defaultdict
from typing import Any

from ycc_hull.config import CONFIG
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.notifications.email_message_builder import EmailMessageBuilder
from ycc_hull.controllers.notifications.format_utils import (
    format_helper_task,
    format_helper_task_min_max_helpers,
    format_helper_task_subject,
    format_helper_task_timing,
    format_helper_tasks_list,
    format_member_info,
    wrap_email_html,
)
from ycc_hull.controllers.notifications.smtp import SmtpConnection
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import HelperTaskDto
from ycc_hull.models.user import User
from ycc_hull.utils import DiffEntry, camel_case_to_words, full_type_name

NOTIFICATION_DELAY_SECONDS = 0.5

_BOAT_PARTY = "⛵️🥳"
_DEAR_SAILORS = f"<p>Dear Sailors {_BOAT_PARTY},</p>"


class _HelperTaskChanges:
    def __init__(
        self,
        old_task: HelperTaskDto,
        new_task: HelperTaskDto,
        diff: dict[str, DiffEntry],
    ):
        self._logger = logging.getLogger(full_type_name(self.__class__))

        self._old_task = old_task
        self._new_task = new_task
        # Objects should work on their own copy of the diff
        self._diff = copy.deepcopy(diff)

        self._category_title_change = self._diff.pop("category.title", None)
        self._title_change = self._diff.pop("title", None)
        self._short_description_change = self._diff.pop("shortDescription", None)
        self._long_description_changed = (
            self._diff.pop("longDescription", None) is not None
        )
        self._contact_changed = False
        self._timing_changed = False
        self._captain_required_licence_change = self._diff.pop(
            "captainRequiredLicenceInfo.licence", None
        )
        self._helper_min_max_count_changed = False
        self._urgent_changed = self._diff.pop("urgent", None) is not None
        self._published_changed = self._diff.pop("published", None) is not None
        self._captain_changed = False
        self._helpers_changed = False
        self._status_changed = False

        self.summary: list[str] = []
        self.relevant_details: dict[str, Any] = {}

        self._detect_changes()
        self._compute_known()
        self._collect_undetected_changes()

    def _add_detailed_change(self, label: str, previous_value: Any) -> None:
        self.summary.append(label)
        self.relevant_details[f"Previous {label}"] = previous_value

    def _detect_changes(self) -> None:
        # Group fields covering the same concept and remove keys we never want to report
        for remaining_key in list(self._diff.keys()):
            if (
                remaining_key == "id"
                or remaining_key.endswith(".id")
                or remaining_key.endswith("Id")
            ):
                self._diff.pop(remaining_key, None)
            elif remaining_key.startswith("category."):
                self._diff.pop(remaining_key, None)
            elif remaining_key.startswith("contact."):
                self._contact_changed = True
                self._diff.pop(remaining_key, None)
            elif (
                remaining_key == "startsAt"
                or remaining_key == "endsAt"
                or remaining_key == "deadline"
            ):
                self._timing_changed = True
                self._diff.pop(remaining_key, None)
            elif remaining_key == "helperMinCount" or remaining_key == "helperMaxCount":
                self._helper_min_max_count_changed = True
                self._diff.pop(remaining_key, None)
            elif remaining_key.startswith("captain."):
                self._captain_changed = True
                self._diff.pop(remaining_key, None)
            elif remaining_key.startswith("helpers."):
                self._helpers_changed = True
                self._diff.pop(remaining_key, None)
            elif (
                remaining_key.startswith("marked_as_done_")
                or remaining_key.startswith("validated_")
                or remaining_key.startswith("validation_")
            ):
                self._status_changed = True
                self._diff.pop(remaining_key, None)

    def _compute_known(self) -> None:
        diff_changes = [
            ("category", self._category_title_change),
            ("title", self._title_change),
            ("short description", self._short_description_change),
            (
                "captain required licence",
                self._captain_required_licence_change,
            ),
        ]

        # None = no formatter, no reported details
        flagged_changes = [
            (
                # Not putting this in the email
                "long description",
                self._long_description_changed,
                None,
            ),
            (
                "contact",
                self._contact_changed,
                lambda: format_member_info(self._old_task.contact),
            ),
            (
                "timing",
                self._timing_changed,
                lambda: format_helper_task_timing(self._old_task),
            ),
            (
                "helpers needed",
                self._helper_min_max_count_changed,
                lambda: format_helper_task_min_max_helpers(self._old_task),
            ),
            (
                "urgent" if self._new_task.urgent else "not urgent",
                self._urgent_changed,
                None,
            ),
            (
                "published" if self._new_task.published else "unpublished",
                self._published_changed,
                None,
            ),
            ("captain", self._captain_changed, None),
            ("helpers", self._helpers_changed, None),
            ("status", self._status_changed, None),
        ]

        for label, change in diff_changes:
            if change:
                self._add_detailed_change(label, change["old"])

        for label, flag, get_previous_value in flagged_changes:
            if flag:
                if get_previous_value:
                    self._add_detailed_change(label, get_previous_value())
                else:
                    self.summary.append(label)

    def _collect_undetected_changes(self) -> None:
        for remaining_key in self._diff.keys():
            self._logger.warning(
                "Unhandled field for task update notification: %s", remaining_key
            )
            what = camel_case_to_words(remaining_key)
            self.summary.append(what)
            self.relevant_details[f"Previous {what}"] = self._diff[remaining_key]["old"]


class HelpersNotificationsController(BaseController):
    """
    Controller for sending helper task notifications.
    """

    async def on_update(
        self,
        old_task: HelperTaskDto,
        new_task: HelperTaskDto,
        diff: dict[str, DiffEntry],
        user: User,
    ) -> None:
        if not CONFIG.emails_enabled(self._logger):
            return

        changes = _HelperTaskChanges(old_task, new_task, diff)

        if changes.summary:
            changes_str = f"Here is what changed: {', '.join(changes.summary)}."
        else:
            changes_str = "Nothing seems to have changed — but it's still worth checking in the app! 😊"

        previous_values_html = ""
        if changes.relevant_details:
            previous_values_html = f"""
<p>Details:</p>

<table>
    {"\n".join(f"  <tr><td>{key}</td><td>{value}</td></tr>" for key, value in changes.relevant_details.items())}
</table>
"""

        message = (
            _task_notification_email_to_all_participants(new_task, user, old_task)
            .content(
                wrap_email_html(
                    f"""
{_DEAR_SAILORS}

<p>{user.full_name} has updated this task. 📢</p>

<p>{changes_str}</p>

{format_helper_task(new_task)}

{previous_values_html}
"""
                )
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def on_sign_up(self, task: HelperTaskDto, user: User) -> None:
        if not CONFIG.emails_enabled(self._logger):
            return

        message = (
            _sign_up_email(task, user)
            .content(
                wrap_email_html(
                    f"""
<p>Dear {user.first_name} {_BOAT_PARTY},</p>

<p>Thank you for signing up for this task. 🙏</p>

{format_helper_task(task)}
"""
                )
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def on_mark_as_done(self, task: HelperTaskDto, user: User) -> None:
        if not CONFIG.emails_enabled(self._logger):
            return

        message = (
            _task_notification_email_to_all_participants(task, user)
            .content(
                wrap_email_html(
                    f"""
{_DEAR_SAILORS}

<p>Thank you for your help with this task. {user.full_name} has marked it as done and it is now waiting for validation from {task.contact.full_name}. 🙏</p>

{format_helper_task(task)}
"""
                )
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def on_validate(self, task: HelperTaskDto, user: User) -> None:
        if not CONFIG.emails_enabled(self._logger):
            return

        message = (
            _task_notification_email_to_all_participants(task, user)
            .content(
                wrap_email_html(
                    f"""
{_DEAR_SAILORS}

<p>Thank you for your help with this task, it has been validated by {user.full_name}. 🙏</p>

{format_helper_task(task)}
"""
                )
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def send_reminders(
        self,
        upcoming_tasks: list[HelperTaskDto],
        overdue_tasks: list[HelperTaskDto],
    ) -> None:
        if not CONFIG.emails_enabled(self._logger):
            return

        async with SmtpConnection() as smtp:
            for task in upcoming_tasks:
                await self._send_upcoming_task_reminder(task, smtp)
                await asyncio.sleep(NOTIFICATION_DELAY_SECONDS)

            overdue_tasks_by_contact_id: dict[int, list[HelperTaskDto]] = defaultdict(
                list
            )
            for task in overdue_tasks:
                overdue_tasks_by_contact_id[task.contact.id].append(task)

            for _, tasks in overdue_tasks_by_contact_id.items():
                if not tasks:
                    continue

                contact = tasks[0].contact
                await self._send_overdue_tasks_reminder(contact, tasks, smtp)
                await asyncio.sleep(NOTIFICATION_DELAY_SECONDS)

    async def _send_upcoming_task_reminder(
        self, task: HelperTaskDto, smtp: SmtpConnection
    ) -> None:
        warnings = _get_task_warnings(task)

        message_builder = _task_notification_email_to_captain_and_helpers(task)

        if warnings:
            message_builder.to(task.contact)

        message = message_builder.content(
            f"""
{_DEAR_SAILORS}

<p>This is just a quick reminder about your upcoming task. 🔔</p>

{format_helper_task(task, warnings=warnings)}
            """
        ).build()
        await smtp.send_message(message)

    async def _send_overdue_tasks_reminder(
        self,
        contact: MemberPublicInfoDto,
        tasks: list[HelperTaskDto],
        smtp: SmtpConnection,
    ) -> None:
        if not tasks:
            return

        tasks_count = len(tasks)
        n_overdue_tasks_str = (
            f"{tasks_count} overdue task{'s' if tasks_count > 1 else ''}"
        )

        message = (
            EmailMessageBuilder()
            .to(contact)
            .reply_to(contact)
            .subject(f"⛵⏰ {n_overdue_tasks_str}")
            .content(
                f"""
<p>Dear {contact.first_name} {_BOAT_PARTY},</p>

<p>This is a reminder that you are the contact for {n_overdue_tasks_str}. ⏰</p>

{format_helper_tasks_list(tasks)}

<p>You can:</p>

<ul>
    <li>Validate the tasks. During validation you will be asked to mark which members showed up and optionally you can leave a comment.</li>
    <li>If the task was not done before the deadline, maybe you want to extend it to allow more time for helpers to do it.</li>
    <li>If you wish to cancel a task, you can do it by validating it (feel free to comment that it is cancelled).</li>
    <li>If you wish to delete a task, please cancel it instead.</li>
</ul>
"""
            )
        ).build()

        await smtp.send_message(message)


def _sign_up_email(task: HelperTaskDto, user: User) -> EmailMessageBuilder:
    return (
        EmailMessageBuilder()
        .to(user)
        .cc(task.contact)
        .cc(task.captain.member if task.captain else None)
        .reply_to(task.contact)
        .subject(format_helper_task_subject(task))
    )


def _task_notification_email(task: HelperTaskDto) -> EmailMessageBuilder:
    return (
        EmailMessageBuilder()
        .reply_to(task.contact)
        .subject(format_helper_task_subject(task))
    )


def _task_notification_email_to_all_participants(
    task: HelperTaskDto, user: User | None, old_task: HelperTaskDto | None = None
) -> EmailMessageBuilder:

    builder = (
        _task_notification_email(task)
        .to(task.contact)
        .to(task.captain.member if task.captain else None)
        .to(helper.member for helper in task.helpers)
        # It can be an admin who is not on the task
        .cc(user)
    )

    if old_task:
        builder.cc(old_task.contact).cc(
            old_task.captain.member if old_task.captain else None
        ).cc(helper.member for helper in old_task.helpers)

    return builder


def _task_notification_email_to_captain_and_helpers(
    task: HelperTaskDto,
) -> EmailMessageBuilder:
    return (
        _task_notification_email(task)
        .to(task.captain.member if task.captain else None)
        .to(helper.member for helper in task.helpers)
    )


def _get_task_warnings(task: HelperTaskDto) -> list[str]:
    warnings = []

    if not task.captain:
        warnings.append("No captain has signed up.")

    helper_count = len(task.helpers)
    if helper_count < task.helper_min_count:
        helper_count_str: str = ""

        if helper_count == 0:
            helper_count_str = "No helpers have"
        elif helper_count == 1:
            helper_count_str = "Only 1 helper has"
        else:
            helper_count_str = f"Only {helper_count} helpers have"

        required_helpers_str = (
            "1 is" if task.helper_min_count == 1 else f"{task.helper_min_count} are"
        )

        warnings.append(
            f"{helper_count_str} signed up &mdash; at least {required_helpers_str} required."
        )

    return warnings
