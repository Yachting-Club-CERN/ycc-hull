"""Helpers notification controller."""

import asyncio
import copy
import logging
import random
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from html import escape
from typing import Any

from ycc_hull.config import CONFIG
from ycc_hull.constants import ATTACHMENT_NOTIFICATION_DEBOUNCE_SECONDS
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.notifications.email_message_builder import EmailMessageBuilder
from ycc_hull.controllers.notifications.format_utils import (
    format_helper_task,
    format_helper_task_min_max_helpers,
    format_helper_task_subject,
    format_helper_task_timing,
    format_helper_tasks_list,
    format_member_info,
)
from ycc_hull.controllers.notifications.smtp import SmtpConnection
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import HelperTaskDto
from ycc_hull.models.user import User
from ycc_hull.utils import DiffEntry, camel_case_to_words, full_type_name

NOTIFICATION_DELAY_SECONDS = 0.5

_BOAT_PARTY = "⛵️🥳"
_DEAR_SAILORS = f"<p>Dear Sailors {_BOAT_PARTY},</p>"
_SIGN_UP_MESSAGES = [
    "Thank you for signing up for this task! 🙌",
    "Thanks for taking on this task — we appreciate it! 🙏",
    "Thank you for stepping up to help the Club with this task! 💪",
    "Big thanks for jumping in to help out with this task! 👏",
]

_BRAVO_ZULU_THANK_YOU = """
<p>Bravo Zulu! Your help keeps the Club sailing smoothly! Thank you! 🙏</p>
"""
_SHIFT_REPLACEMENT_REMINDER = """
<p>
    <em>If you need to withdraw from a task, please find a replacement first (e.g., in
    one of the WhatsApp groups), then notify the contact by email (and CC your
    replacement). The contact will administer the change.</em>
</p>
"""
_SIGNATURE = """
<p>
    Fair Winds,<br />
    YCC
</p>
"""


class _AttachmentAction(StrEnum):
    UPLOAD = "upload"
    DELETE = "delete"


# Debounce key: (task_id, user_member_id, action)
_AttachmentDebounceKey = tuple[int, int, _AttachmentAction]


@dataclass
class _AttachmentDebounceBucket:
    """Collects attachment filenames while waiting for the debounce timer."""

    task: HelperTaskDto
    user: User
    action: _AttachmentAction
    filenames: list[str] = field(default_factory=list)
    timer_handle: asyncio.TimerHandle | None = None


class _HelperTaskChanges:
    """Responsible for computing the changes between two helper tasks.

    Attributes:
        summary (list[str]): A list of labels representing the fields that have
            changed.
        relevant_details (dict[str, Any]): A dictionary mapping descriptive labels to
            values.

    """

    def __init__(
        self,
        original_task: HelperTaskDto,
        updated_task: HelperTaskDto,
        diff: dict[str, DiffEntry],
    ) -> None:
        self._logger = logging.getLogger(full_type_name(self.__class__))

        self._original_task = original_task
        self._updated_task = updated_task
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

    def _add_detailed_change(
        self,
        label: str,
        previous_value: Any,  # noqa: ANN401
    ) -> None:
        self.summary.append(label)
        self.relevant_details[f"Previous {label}"] = previous_value

    def _detect_changes(self) -> None:
        # Group fields covering the same concept and remove keys we never want to report
        for remaining_key in list(self._diff.keys()):
            if (
                remaining_key == "id"
                or remaining_key.endswith((".id", "Id"))
                or remaining_key.startswith("category.")
            ):
                self._diff.pop(remaining_key)
            elif remaining_key.startswith("contact."):
                self._contact_changed = True
                self._diff.pop(remaining_key)
            elif remaining_key in {"startsAt", "endsAt", "deadline"}:
                self._timing_changed = True
                self._diff.pop(remaining_key)
            elif remaining_key in {"helperMinCount", "helperMaxCount"}:
                self._helper_min_max_count_changed = True
                self._diff.pop(remaining_key)
            elif remaining_key.startswith("captain."):
                self._captain_changed = True
                self._diff.pop(remaining_key)
            elif remaining_key.startswith("helpers."):
                self._helpers_changed = True
                self._diff.pop(remaining_key)
            elif remaining_key.startswith(
                ("marked_as_done_", "validated_", "validation_")
            ):
                self._status_changed = True
                self._diff.pop(remaining_key)

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
                lambda: format_member_info(self._original_task.contact),
            ),
            (
                "timing",
                self._timing_changed,
                lambda: format_helper_task_timing(self._original_task),
            ),
            (
                "helpers needed",
                self._helper_min_max_count_changed,
                lambda: format_helper_task_min_max_helpers(self._original_task),
            ),
            (
                "urgent" if self._updated_task.urgent else "not urgent",
                self._urgent_changed,
                None,
            ),
            (
                "published" if self._updated_task.published else "unpublished",
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
        for remaining_key in self._diff:
            self._logger.warning(
                "Unhandled field for task update notification: %s", remaining_key
            )
            what = camel_case_to_words(remaining_key)
            self.summary.append(what)
            self.relevant_details[f"Previous {what}:"] = self._diff[remaining_key][
                "old"
            ]


class HelpersNotificationsController(BaseController):
    """Controller for sending helper task notifications."""

    def __init__(self) -> None:
        """Initialise the controller."""
        super().__init__()
        self._attachment_debounce: dict[
            _AttachmentDebounceKey, _AttachmentDebounceBucket
        ] = {}

    async def on_update(
        self,
        original_task: HelperTaskDto,
        updated_task: HelperTaskDto,
        diff: dict[str, DiffEntry],
        user: User,
    ) -> None:
        """Notify signed up members about a task update."""
        if not CONFIG.emails_enabled(self._logger):
            return

        changes = _HelperTaskChanges(original_task, updated_task, diff)

        if changes.summary:
            changes_str = f"Here is what changed: {', '.join(changes.summary)}."
        else:
            changes_str = (
                "Nothing seems to have changed — but it's still worth checking in the "
                "app! 😊"
            )

        previous_values_html = ""
        if changes.relevant_details:
            previous_values_html = f"""
<p style="font-size: small;">Change details:</p>

<table style="font-size: small;">
    {
                "\n".join(
                    f"  <tr><td>{key}</td><td>{value}</td></tr>"
                    for key, value in changes.relevant_details.items()
                )
            }
</table>
"""

        message = (
            _task_notification_email_to_all_participants(
                updated_task, user, original_task
            )
            .content(
                f"""
{_DEAR_SAILORS}

<p>{user.full_name} has updated this task. 📢</p>

<p>{changes_str}</p>

{format_helper_task(updated_task)}

{_SHIFT_REPLACEMENT_REMINDER}
{_SIGNATURE}

{previous_values_html}
"""
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def on_add_helper(
        self, task: HelperTaskDto, helper: MemberPublicInfoDto, user: User
    ) -> None:
        """Notify about a helper being added to a task."""
        if not CONFIG.emails_enabled(self._logger):
            return

        message = (
            _add_or_remove_helper_email(task, helper, user)
            .content(
                f"""
<p>Dear {helper.first_name} {_BOAT_PARTY},</p>

<p>{user.full_name} has added you to this task.</p>

{format_helper_task(task)}

{_SHIFT_REPLACEMENT_REMINDER}
{_SIGNATURE}
"""
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def on_remove_helper(
        self, task: HelperTaskDto, helper: MemberPublicInfoDto, user: User
    ) -> None:
        """Notify about a helper being removed from a task."""
        if not CONFIG.emails_enabled(self._logger):
            return

        message = (
            _add_or_remove_helper_email(task, helper, user)
            .content(
                f"""
<p>Dear {helper.first_name} {_BOAT_PARTY},</p>

<p>{user.full_name} has removed you from this task.</p>

{format_helper_task(task)}

{_SHIFT_REPLACEMENT_REMINDER}
{_SIGNATURE}
"""
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def on_sign_up(self, task: HelperTaskDto, user: User) -> None:
        """Notify the contact about a member sign-up."""
        if not CONFIG.emails_enabled(self._logger):
            return

        sign_up_message = random.choice(_SIGN_UP_MESSAGES)  # noqa: S311

        message = (
            _sign_up_email(task, user)
            .content(
                f"""
<p>Dear {user.first_name} {_BOAT_PARTY},</p>

<p>{sign_up_message}</p>

{format_helper_task(task)}

{_SHIFT_REPLACEMENT_REMINDER}
{_SIGNATURE}
"""
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def on_mark_as_done(self, task: HelperTaskDto, user: User) -> None:
        """Notify about a task being marked as done."""
        if not CONFIG.emails_enabled(self._logger):
            return

        message = (
            _task_notification_email_to_all_participants(task, user)
            .content(
                f"""
{_DEAR_SAILORS}

{_BRAVO_ZULU_THANK_YOU}
<p>{user.full_name} has marked this task as done and it is now waiting for validation
from {task.contact.full_name}.</p>

{format_helper_task(task)}

{_SIGNATURE}
"""
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def on_validate(self, task: HelperTaskDto, user: User) -> None:
        """Notify about a task being validated."""
        if not CONFIG.emails_enabled(self._logger):
            return

        message = (
            _task_notification_email_to_all_participants(task, user)
            .content(
                f"""
{_DEAR_SAILORS}

{_BRAVO_ZULU_THANK_YOU}
<p>This task has been validated by {user.full_name}.</p>

{format_helper_task(task)}

{_SIGNATURE}
"""
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    def on_attachment_upload(
        self, task: HelperTaskDto, filename: str, user: User
    ) -> None:
        """Buffer an attachment upload notification (debounced)."""
        self._debounce_attachment(task, filename, user, _AttachmentAction.UPLOAD)

    def on_attachment_delete(
        self, task: HelperTaskDto, filename: str, user: User
    ) -> None:
        """Buffer an attachment delete notification (debounced)."""
        self._debounce_attachment(task, filename, user, _AttachmentAction.DELETE)

    def _debounce_attachment(
        self,
        task: HelperTaskDto,
        filename: str,
        user: User,
        action: _AttachmentAction,
    ) -> None:
        if not CONFIG.emails_enabled(self._logger):
            return

        key: _AttachmentDebounceKey = (task.id, user.member_id, action)
        bucket = self._attachment_debounce.get(key)

        if bucket is None:
            bucket = _AttachmentDebounceBucket(task=task, user=user, action=action)
            self._attachment_debounce[key] = bucket

        bucket.filenames.append(filename)
        # Always keep the latest task snapshot (participants may have changed)
        bucket.task = task

        if bucket.timer_handle is not None:
            bucket.timer_handle.cancel()

        loop = asyncio.get_running_loop()
        bucket.timer_handle = loop.call_later(
            ATTACHMENT_NOTIFICATION_DEBOUNCE_SECONDS,
            lambda k=key: self._run_in_background(self._flush_attachment(k)),
        )

        self._logger.info(
            "Attachment %s debounced: task=%d, user=%s, filename=%r, "
            "queued=%d, debounce=%ds",
            action.value,
            task.id,
            user.username,
            filename,
            len(bucket.filenames),
            ATTACHMENT_NOTIFICATION_DEBOUNCE_SECONDS,
        )

    async def _flush_attachment(self, key: _AttachmentDebounceKey) -> None:
        bucket = self._attachment_debounce.pop(key, None)
        if bucket is None:
            return

        task = bucket.task
        user = bucket.user
        filenames = bucket.filenames
        count = len(filenames)
        filenames_html = ", ".join(f"<strong>{escape(f)}</strong>" for f in filenames)

        if bucket.action == _AttachmentAction.UPLOAD:
            if count == 1:
                action_text = (
                    f"{user.full_name} has added an attachment to this task: "
                    f"{filenames_html} 📸"
                )
            else:
                action_text = (
                    f"{user.full_name} has added {count} attachments to this task: "
                    f"{filenames_html} 📸"
                )
        elif count == 1:
            action_text = (
                f"{user.full_name} has removed an attachment from this task: "
                f"{filenames_html}"
            )
        else:
            action_text = (
                f"{user.full_name} has removed {count} attachments from this task: "
                f"{filenames_html}"
            )

        message = (
            _task_notification_email_to_all_participants(task, user)
            .content(
                f"""
{_DEAR_SAILORS}

<p>{action_text}</p>

{format_helper_task(task)}

{_SIGNATURE}
"""
            )
            .build()
        )

        self._logger.info(
            "Sending batched attachment %s notification: task=%d, user=%s, "
            "filenames=[%s]",
            bucket.action.value,
            task.id,
            user.username,
            ", ".join(repr(f) for f in filenames),
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def send_reminders(
        self,
        upcoming_tasks: list[HelperTaskDto],
        overdue_tasks: list[HelperTaskDto],
    ) -> None:
        """Send reminder emails for upcoming and overdue tasks."""
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

            for tasks in overdue_tasks_by_contact_id.values():
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
    <li>If a task has been completed, please validate it.</li>
    <li>If more time is needed, you can extend the deadline.</li>
    <li>If the task is no longer necessary, feel free to cancel it by validating it and
    leaving a comment.</li>
</ul>

{_SHIFT_REPLACEMENT_REMINDER}
{_SIGNATURE}
"""
            )
        ).build()

        await smtp.send_message(message)


def _add_or_remove_helper_email(
    task: HelperTaskDto, helper: MemberPublicInfoDto, user: User
) -> EmailMessageBuilder:
    return (
        EmailMessageBuilder()
        .to(helper)
        .cc(task.contact)
        .cc(task.captain.member if task.captain else None)
        .cc(user)
        .reply_to(task.contact)
        .subject(format_helper_task_subject(task))
    )


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
    task: HelperTaskDto, user: User | None, original_task: HelperTaskDto | None = None
) -> EmailMessageBuilder:

    builder = (
        _task_notification_email(task)
        .to(task.contact)
        .to(task.captain.member if task.captain else None)
        .to(helper.member for helper in task.helpers)
        # It can be an admin who is not on the task
        .cc(user)
    )

    if original_task:
        builder.cc(original_task.contact).cc(
            original_task.captain.member if original_task.captain else None
        ).cc(helper.member for helper in original_task.helpers)

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
            f"{helper_count_str} signed up &mdash; at least {required_helpers_str} "
            "required."
        )

    return warnings
