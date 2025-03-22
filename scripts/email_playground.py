"""
Email playground.
"""

import asyncio
from email.message import EmailMessage

from ycc_hull.config import CONFIG
from ycc_hull.controllers.notifications.email_content_utils import format_helper_task
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
    starts_at="2024-04-25T18:00:00Z",
    ends_at="2024-04-25T20:30:00Z",
    deadline=None,
    urgent=False,
    captain_required_licence_info=LicenceInfoDto(id=9, licence="M"),
    helper_min_count=1,
    helper_max_count=2,
    published=True,
    captain=HelperTaskHelperDto(
        member=member_bob,
        signed_up_at="2024-04-01T09:00:00Z",
    ),
    helpers=[
        HelperTaskHelperDto(
            member=member_john,
            signed_up_at="2024-04-01T09:01:00Z",
        ),
        HelperTaskHelperDto(
            member=member_marie,
            signed_up_at="2024-04-01T09:02:00Z",
        ),
    ],
    marked_as_done_at=None,
    marked_as_done_by=None,
    marked_as_done_comment=None,
    validated_at=None,
    validated_by=None,
    validation_comment=None,
)


async def send_mail(smtp: SmtpConnection, subject: str, content: str) -> None:
    print("Connecting to SMTP server...")

    email = EmailMessage()
    email["From"] = CONFIG.email.from_email
    email["To"] = CONFIG.email.from_email
    email["Subject"] = subject
    email.set_content(content)

    print("Sending email...")
    await smtp.send_message(email)
    print("Email sent.")


async def run() -> None:
    print("Connecting to SMTP server...")

    async with SmtpConnection() as smtp:
        await send_mail(smtp, "Test - Hello, world!", "Hello, world!")

        await send_mail(
            smtp,
            "Test - HTML",
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
        )

        await send_mail(
            smtp,
            "Test - Helper Task",
            f"""
<html>
<body>
<table
    role="presentation"
    border="0"
    cellpadding="0"
    cellspacing="0"
    width="100%"
    style="font-family: 'Roboto', 'Helvetica', 'Arial', sans-serif;"
>
    <tr>
        <td>{format_helper_task(helper_task)}</td>
    </tr>
</table>
</body>
</html>
""",
        )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
