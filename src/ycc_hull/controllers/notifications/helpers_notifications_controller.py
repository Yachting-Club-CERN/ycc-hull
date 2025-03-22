from ycc_hull.config import CONFIG
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.notifications.email_message_builder import EmailMessageBuilder
from ycc_hull.controllers.notifications.format_utils import (
    format_helper_task,
    format_helper_task_subject,
    wrap_email_html,
)
from ycc_hull.controllers.notifications.smtp import SmtpConnection
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
            _task_notification_email(task, user)
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
            _task_notification_email(task, user)
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


def _sign_up_email(task: HelperTaskDto, user: User) -> EmailMessageBuilder:
    return (
        EmailMessageBuilder()
        .to(user)
        .cc(task.contact)
        .cc(task.captain.member if task.captain else None)
        .reply_to(task.contact)
        .subject(format_helper_task_subject(task))
    )


def _task_notification_email(
    task: HelperTaskDto, user: User | None
) -> EmailMessageBuilder:
    return (
        EmailMessageBuilder()
        .to(task.contact)
        .to(task.captain.member if task.captain else None)
        .to(helper.member for helper in task.helpers)
        # It can be an admin too who is not on the task
        .cc(user)
        .reply_to(task.contact)
        .subject(format_helper_task_subject(task))
    )
