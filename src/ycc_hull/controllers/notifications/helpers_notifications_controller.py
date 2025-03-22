from enum import Enum
from re import M

from ycc_hull.config import CONFIG
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.notifications.email_content_utils import (
    SHIFT_REPLACEMENT_REMINDER,
    YCC_APP_SIGNATURE,
    format_helper_task,
    format_helper_task_subject,
    wrap_email_html,
)
from ycc_hull.controllers.notifications.email_message_builder import EmailMessageBuilder
from ycc_hull.controllers.notifications.smtp import SmtpConnection
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import HelperTaskDto, HelperTaskHelperDto
from ycc_hull.models.user import User


class HelpersNotificationsController(BaseController):
    async def on_task_sign_up(self, task: HelperTaskDto, user: User) -> None:
        message = (
            EmailMessageBuilder()
            .to(user)
            .cc(task.contact)
            .cc(task.captain.member if task.captain else None)
            .reply_to(task.contact)
            .subject(format_helper_task_subject(task))
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


#     async def on_task_marked_as_done(
#         self, task: HelperTaskDto, user: User
#     ) -> None:
#         user.
#         message = (
#             EmailMessageBuilder()
#             .to(task.contact)
#             .to(task.captain.member if task.captain else None)
#             .to(helper.member for helper in task.helpers)
#             .cc(marked_as_done_by)  # It can be an admin too who is not on the task
#             .reply_to(task.contact)
#             .subject(format_helper_task_subject(task))
#             .content(
#                 wrap_email_html(
#                     f"""
# <p>Dear Helpers,</p>

# <p>Thank you for helping out with this task. It has been marked as done by {marked_as_done_by.full_name)</p>
# """
#                 )
#             )
#         )
