from collections import defaultdict
from typing import Iterable

from ycc_hull.config import CONFIG
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.notifications.email_message_builder import (
    EmailContact,
    EmailContacts,
    EmailMessageBuilder,
)
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


class HelpersNotificationsController(BaseController):
    """
    Controller for sending helper task notifications.
    """

    async def on_sign_up(self, task: HelperTaskDto, user: User) -> None:
        if not CONFIG.email:
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
        if not CONFIG.email:
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
        if not CONFIG.email:
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
        # TODO logging
        if not CONFIG.email:
            return

        async with SmtpConnection() as smtp:
            for task in upcoming_tasks:
                await self._send_upcoming_task_reminder(task, smtp)

            overdue_tasks_by_contact_id: dict[int, list[HelperTaskDto]] = defaultdict(
                list
            )
            for task in overdue_tasks:
                overdue_tasks_by_contact_id[task.contact.id].append(task)

            for contact_id, tasks in overdue_tasks_by_contact_id.items():
                if not tasks:
                    continue

                contact = tasks[0].contact
                await self._send_overdue_tasks_reminder(contact, tasks, smtp)

    async def _send_upcoming_task_reminder(
        self, task: HelperTaskDto, smtp: SmtpConnection
    ) -> None:
        message = (
            _task_notification_email_to_captain_and_helpers(task)
            .content(
                f"""
<p>Dear Sailors,</p>

<p>This just a quick reminder about your upcoming task.</p>

{format_helper_task(task)}
            """
            )
            .build()
        )
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
        n_overdue_tasks = f"{tasks_count} overdue task{'s' if tasks_count > 1 else ''}"

        message = (
            EmailMessageBuilder()
            .to(contact)
            .reply_to(contact)
            .subject(n_overdue_tasks)
            .content(
                f"""
<p>Dear {contact.first_name},</p>

<p>This is a reminder you are the contact for {n_overdue_tasks}.</p>

{format_helper_tasks_list(tasks)}

<p>You can:</p>

<ul>
    <li>Validate the tasks. During validation you will be asked to mark which members showed up and optionally you can leave a comment</li>
    <li>If the task was not done before the deadline, maybe you want to extend it.</li>
</ul>
"""mo
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
