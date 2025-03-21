"""
Email playground.
"""

import asyncio
from email.message import EmailMessage

from ycc_hull.config import CONFIG
from ycc_hull.controllers.notifications.smtp import SmtpConnection


async def run() -> None:
    print("Connecting to SMTP server...")

    async with SmtpConnection() as smtp:
        email = EmailMessage()
        email["From"] = CONFIG.email.from_email
        email["To"] = CONFIG.email.from_email
        email["Subject"] = "Test #1"
        email.set_content("Hello, world!")

        print("Sending email...")
        await smtp.send_message(email)
        print("Email sent.")

        email = EmailMessage()
        email["From"] = CONFIG.email.from_email
        email["To"] = CONFIG.email.from_email
        email["Subject"] = "Test #2"
        email.set_content(
            """
<html>
<body>
<p>HTML TEST</p>

<p><strong>STRONG</strong> <em>EM</em> <u>U</u> <s>S</s> <a href="https://ycc.app.cern.ch">A</a></p>
<p><b>BOLD</b> <i>ITALIC</i> <u>UNDERLINE</u> <s>STRIKETHROUGH</s></p>

<p><span style="color: red;">RED</span> <span style="color: green;">GREEN</span> <span style="color: blue;">BLUE</span></p>
<p><span style="font-size: 20px;">20px</span> <span style="font-size: 30px;">30px</span> <span style="font-size: 40px;">40px</span></p>
<p><span style="font-family: Arial;">Arial</span> <span style="font-family: Courier;">Courier</span> <span style="font-family: Georgia;">Georgia</span></p>
<p><span style="font-weight: bold;">BOLD</span> <span style="font-style: italic;">ITALIC</span> <span style="text-decoration: underline;">UNDERLINE</span></p>
</body>
</html>
"""
        )

        print("Sending email...")
        await smtp.send_message(email)
        print("Email sent.")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
