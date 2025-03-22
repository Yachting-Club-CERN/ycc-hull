from enum import Enum
from re import M
from ycc_hull.config import CONFIG
from ycc_hull.controllers.notifications.email import EmailMessageBuilder
from ycc_hull.controllers.notifications.email_content_utils import (
    SHIFT_REPLACEMENT_REMINDER,
    YCC_APP_SIGNATURE,
    format_helper_task,
    format_helper_task_subject,
    wrap_email_html,
)
from ycc_hull.controllers.notifications.smtp import SmtpConnection
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import HelperTaskDto, HelperTaskHelperDto


class HelpersNotificationsController:
    async def on_task_sign_up(
        self, task: HelperTaskDto, signed_up_member: MemberPublicInfoDto
    ) -> None:
        message = (
            EmailMessageBuilder()
            .to(signed_up_member)
            .cc(task.contact)
            .cc(task.captain.member if task.captain else None)
            .reply_to(task.contact)
            .subject(format_helper_task_subject(task))
            .content(
                wrap_email_html(
                 f"""
<p>Dear {task.captain.member.first_name},</p>
<p>Thank you for signing up for this task.</p>

{format_helper_task(task)}
"""
                )
            )
            .build()
        )

        async with SmtpConnection() as smtp:
            smtp.send_message(message)
            
    async def on_task_marked_as_done(
        self, task: HelperTaskDto
    ) -> None:
        message = (
            EmailMessageBuilder()
            .to(task.contact)
            .cc(task.captain.member if task.captain else None)
            .cc(helper.member for helper in task.helpers)
            .reply_to(helper.member)
            .subject(format_helper_task_subject(task))
            .content(
                wrap_email_html(
                    f"""
