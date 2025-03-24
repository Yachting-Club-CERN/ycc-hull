import asyncio
from collections import defaultdict

from ycc_hull.config import emails_enabled
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.notifications.email_message_builder import EmailMessageBuilder
from ycc_hull.controllers.notifications.format_utils import (
    format_helper_task,
    format_helper_task_subject,
    format_helper_tasks_list,
    wrap_email_html,
)
from ycc_hull.controllers.notifications.smtp import SmtpConnection
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import HelperTaskDto
from ycc_hull.models.user import User

NOTIFICATION_DELAY_SECONDS = 0.5


class HelpersNotificationsController(BaseController):
    """
    Controller for sending helper task notifications.
    """

    async def on_sign_up(self, task: HelperTaskDto, user: User) -> None:
        if not emails_enabled(self._logger):
            return

        message = (
            _sign_up_email(task, user)
            .content(
                wrap_email_html(
                    f"""
<p>Dear {user.first_name},</p>

<p>Thank you for signing up for this task.</p>

{format_helper_task(task)}
"""
                )
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def on_mark_as_done(self, task: HelperTaskDto, user: User) -> None:
        if not emails_enabled(self._logger):
            return

        message = (
            _task_notification_email_to_all_participants(task, user)
            .content(
                wrap_email_html(
                    f"""
<p>Dear Sailors,</p>

<p>Thank you for your help with this task. {user.full_name} has marked it as done and it is now waiting for validation from {task.contact.full_name}.</p>

{format_helper_task(task)}
"""
                )
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            await smtp.send_message(message)

    async def on_validate(self, task: HelperTaskDto, user: User) -> None:
        if not emails_enabled(self._logger):
            return

        message = (
            _task_notification_email_to_all_participants(task, user)
            .content(
                wrap_email_html(
                    f"""
<p>Dear Sailors,</p>

<p>Thank you for your help with this task, it has been validated by {user.full_name}.</p>

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
        if not emails_enabled(self._logger):
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
<p>Dear Sailors,</p>

<p>This is just a quick reminder about your upcoming task.</p>

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
            .subject(n_overdue_tasks_str)
            .content(
                f"""
<p>Dear {contact.first_name},</p>

<p>This is a reminder that you are the contact for {n_overdue_tasks_str}.</p>

{format_helper_tasks_list(tasks)}

<p>You can:</p>

<ul>
    <li>Validate the tasks. During validation you will be asked to mark which members showed up and optionally you can leave a comment</li>
    <li>If the task was not done before the deadline, maybe you want to extend it.</li>
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
    task: HelperTaskDto, user: User | None
) -> EmailMessageBuilder:

    return (
        _task_notification_email(task)
        .to(task.contact)
        .to(task.captain.member if task.captain else None)
        .to(helper.member for helper in task.helpers)
        # It can be an admin who is not on the task
        .cc(user)
    )


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
