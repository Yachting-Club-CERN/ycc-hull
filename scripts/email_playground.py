"""
Email playground.
"""

import asyncio
import secrets
from email.message import EmailMessage

from ycc_hull.config import CONFIG
from ycc_hull.controllers.notifications.email_message_builder import EmailMessageBuilder
from ycc_hull.controllers.notifications.format_utils import (
    format_helper_task,
    format_helper_task_subject,
    wrap_email_html,
)
from ycc_hull.controllers.notifications.smtp import SmtpConnection
from ycc_hull.models.dtos import LicenceInfoDto, MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import (
    HelperTaskCategoryDto,
    HelperTaskDto,
    HelperTaskHelperDto,
)

member_alice = MemberPublicInfoDto(
    id=1000,
    username="ALICE",
    first_name="Alice",
    last_name="Brown",
    email="alice.brown@mailinator.com",
    mobile_phone=None,
    home_phone=None,
    work_phone=None,
)

member_bob = MemberPublicInfoDto(
    id=1001,
    username="BOB",
    first_name="Bob",
    last_name="Green",
    email="bob.green@mailinator.com",
    mobile_phone=None,
    home_phone="0764561230",
    work_phone=None,
)

member_john = MemberPublicInfoDto(
    id=1003,
    username="JOHN",
    first_name="John",
    last_name="Doe",
    email="john.doe@mailinator.com",
    mobile_phone="0041761234567",
    home_phone=None,
    work_phone=None,
)

member_marie = MemberPublicInfoDto(
    id=1004,
    username="MARIE",
    first_name="Marie",
    last_name="Smith",
    email="marie.smith@mailinator.com",
    mobile_phone="+33781234567",
    home_phone="0761234567",
    work_phone="0036301234567",
)

helper_task = HelperTaskDto(
    id=1,
    category=HelperTaskCategoryDto(
        id=1,
        title="Surveillance",
        short_description="Q-boat surveillance shifts",
        long_description=None,
    ),
    title="Thursday Practice",
    short_description="Club night!",
    long_description=None,
    contact=member_alice,
    starts_at="2024-04-25T18:00:00",
    ends_at="2024-04-25T20:30:00",
    deadline=None,
    urgent=False,
    captain_required_licence_info=LicenceInfoDto(id=9, licence="M"),
    helper_min_count=1,
    helper_max_count=2,
    published=True,
    captain=HelperTaskHelperDto(
        member=member_bob,
        signed_up_at="2024-04-01T09:00:00",
    ),
    helpers=[
        HelperTaskHelperDto(
            member=member_john,
            signed_up_at="2024-04-01T09:01:00",
        ),
        HelperTaskHelperDto(
            member=member_marie,
            signed_up_at="2024-04-01T09:02:00",
        ),
    ],
    marked_as_done_at=None,
    marked_as_done_by=None,
    marked_as_done_comment=None,
    validated_at=None,
    validated_by=None,
    validation_comment=None,
)


def create_message(subject: str, content: str) -> EmailMessage:
    if CONFIG.email is None:
        raise ValueError("Email configuration is not set")

    email = EmailMessage()
    email["From"] = CONFIG.email.from_email
    email["To"] = CONFIG.email.from_email
    email["Subject"] = subject
    email.set_content(content)
    return email


async def send_message(smtp: SmtpConnection, email: EmailMessage) -> None:
    print("Sending email...")
    await smtp.send_message(email)
    print("Email sent")


async def run() -> None:
    prefix = f"Test {secrets.token_hex(2).upper()} - "

    print("Connecting to SMTP server...")

    async with SmtpConnection() as smtp:
        print("Connected to SMTP server")

        await send_message(
            smtp, create_message(f"{prefix}Hello, world!", "Hello, world!")
        )

        await send_message(
            smtp,
            create_message(
                f"{prefix}HTML",
                """
<html>
<body>
<p>HTML TEST</p>

<p>
    <strong>STRONG</strong>
    <em>EM</em>
    <u>U</u>
    <s>S</s>
    <a href="https://ycc.app.cern.ch">A</a>
</p>

<p>
    <b>BOLD</b>
    <i>ITALIC</i>
    <u>UNDERLINE</u>
    <s>STRIKETHROUGH</s>
</p>

<p>
    <span style="color: red;">RED</span>
    <span style="color: green;">GREEN</span>
    <span style="color: blue;">BLUE</span>
</p>
<p>
    <span style="font-size: 20px;">20px</span>
    <span style="font-size: 30px;">30px</span>
    <span style="font-size: 40px;">40px</span>
</p>
<p>
    <span>DEFAULT</span>
    <span style="font-size: xx-small;">xx-small</span>
    <span style="font-size: x-small;">x-small</span>
    <span style="font-size: small;">small</span>
    <span style="font-size: medium;">medium</span>
    <span style="font-size: large;">large</span>
    <span style="font-size: x-large;">x-large</span>
    <span style="font-size: xx-large;">xx-large</span>
    <span>DEFAULT</span>
</p>
<p>
    <span style="font-family: Arial;">Arial</span>
    <span style="font-family: Courier;">Courier</span>
    <span style="font-family: Georgia;">Georgia</span>
</p>
<p>
    <span style="font-weight: bold;">BOLD</span>
    <span style="font-style: italic;">ITALIC</span>
    <span style="text-decoration: underline;">UNDERLINE</span>
</p>
</body>
</html>
""",
            ),
        )

        await send_message(
            smtp,
            create_message(
                f"{prefix}Helper Task",
                wrap_email_html(format_helper_task(helper_task)),
            ),
        )

        if helper_task.captain is None:
            raise ValueError(f"Captain is not set: {helper_task}")

        await send_message(
            smtp,
            EmailMessageBuilder().to(helper_task.captain.member).cc(helper_task.contact)
            # CC is removed by the builder if it is the same as TO
            .cc(helper_task.captain.member)
            .cc(helper.member for helper in helper_task.helpers)
            .reply_to(helper_task.contact)
            .subject(f"{prefix}{format_helper_task_subject(helper_task)}")
            .content(
                f"""
<p>Dear {helper_task.captain.member.first_name},</p>
<p>Thank you for signing up for this task.</p>

{format_helper_task(helper_task)}
"""
            )
            .build(),
        )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
