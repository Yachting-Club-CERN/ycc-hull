import asyncio
from collections import defaultdict

from ycc_hull.config import CONFIG
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.notifications.email_message_builder import EmailMessageBuilder
from ycc_hull.controllers.notifications.format_utils import (
    format_helper_task,
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
from ycc_hull.utils import DiffEntry, camel_case_to_words

NOTIFICATION_DELAY_SECONDS = 0.5

_BOAT_PARTY = "⛵️🥳"
_DEAR_SAILORS = f"<p>Dear Sailors {_BOAT_PARTY},</p>"


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

        category_title_change = diff.pop("category.title", None)
        title_change = diff.pop("title", None)
        short_description_change = diff.pop("shortDescription", None)
        long_description_changed = diff.pop("longDescription", None) is not None

        contact_changed = False
        timing_changed = False
        captain_required_licence_change = diff.pop(
            "captainRequiredLicenceInfo.licence", None
        )
        helper_min_max_count_changed = False

        urgent_change = diff.pop("urgent", None)
        published_change = diff.pop("published", None)

        # These are only here for completeness, however, they have their separate API endpoint and notifications
        captain_changed = False
        helpers_changed = False
        status_changed = False

        # Group fields covering the same concept and remove keys we never want to report
        for remaining_key in list(diff.keys()):
            if (
                remaining_key == "id"
                or remaining_key.endswith(".id")
                or remaining_key.endswith("Id")
            ):
                diff.pop(remaining_key, None)
            elif remaining_key.startswith("category."):
                diff.pop(remaining_key, None)
            elif remaining_key.startswith("contact."):
                contact_changed = True
                diff.pop(remaining_key, None)
            elif (
                remaining_key == "startsAt"
                or remaining_key == "endsAt"
                or remaining_key == "deadline"
            ):
                timing_changed = True
                diff.pop(remaining_key, None)
            elif remaining_key == "helperMinCount" or remaining_key == "helperMaxCount":
                helper_min_max_count_changed = True
                diff.pop(remaining_key, None)
            elif remaining_key.startswith("captain."):
                captain_changed = True
                diff.pop(remaining_key, None)
            elif remaining_key.startswith("helpers."):
                helpers_changed = True
                diff.pop(remaining_key, None)
            elif (
                remaining_key.startswith("marked_as_done_")
                or remaining_key.startswith("validated_")
                or remaining_key.startswith("validation_")
            ):
                status_changed = True
                diff.pop(remaining_key, None)

        changes = []
        previous_values = {}

        if category_title_change:
            changes.append("category")
            previous_values["Previous category"] = category_title_change["old"]
        if title_change:
            changes.append("title")
            previous_values["Previous title"] = title_change["old"]
        if short_description_change:
            changes.append("short description")
            previous_values["Previous short description"] = short_description_change[
                "old"
            ]
        if long_description_changed:
            changes.append("long description")
            # Not putting this in the email
        if contact_changed:
            changes.append("contact")
            previous_values["Previous contact"] = format_member_info(old_task.contact)
        if timing_changed:
            changes.append("timing")
            previous_values["Previous timing"] = format_helper_task_timing(old_task)
        if captain_required_licence_change:
            changes.append("captain required licence")
            previous_values["Previous captain required licence"] = (
                captain_required_licence_change["old"]
            )
        if helper_min_max_count_changed:
            changes.append("helpers needed")
            previous_values["Previous helpers needed"] = (
                f"{old_task.helper_min_count} - {old_task.helper_max_count}"
            )
        if urgent_change:
            if new_task.urgent:
                changes.append("urgent")
            else:
                changes.append("not urgent")
        if published_change:
            if new_task.published:
                changes.append("published")
            else:
                changes.append("unpublished")
        if captain_changed:
            changes.append("captain")
        if helpers_changed:
            changes.append("helpers")
        if status_changed:
            changes.append("status")

        for remaining_key in diff.keys():
            self._logger.warning(
                "Unhandled field for task update notification: %s", remaining_key
            )
            what = camel_case_to_words(remaining_key)
            changes.append(what)
            previous_values[f"Previous {what}"] = diff[remaining_key]["old"]

        if changes:
            changes_str = f"Here is what changed: {', '.join(changes)}."
        else:
            changes_str = "Nothing seems to have changed — but it's still worth checking in the app! 😊"

        previous_values_html = ""
        if previous_values:
            previous_values_html = f"""
<p>Previous values:</p>

<table>
    {"\n".join(f"  <tr><td>{key}</td><td>{value}</td></tr>" for key, value in previous_values.items())}
</table>
"""

        message = (
            _task_notification_email_to_all_participants(new_task, user, old_task)
            .content(
                wrap_email_html(
                    f"""
{_DEAR_SAILORS}

<p>🆕 {user.full_name} has updated this task.</p>

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

<p>🙏 Thank you for signing up for this task.</p>

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

<p>🙏 Thank you for your help with this task. {user.full_name} has marked it as done and it is now waiting for validation from {task.contact.full_name}.</p>

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

<p>🙏 Thank you for your help with this task, it has been validated by {user.full_name}.</p>

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

<p>🔔 This is just a quick reminder about your upcoming task.</p>

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

<p>⏰ This is a reminder that you are the contact for {n_overdue_tasks_str}.</p>

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
