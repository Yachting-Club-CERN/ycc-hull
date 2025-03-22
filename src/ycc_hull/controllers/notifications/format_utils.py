"""
Utility functions for formatting email content.

One could use jinja2, but would need to configure all the helpers too, which are in the end would be in Python anyway.
"""

from datetime import datetime

import phonenumbers

from ycc_hull.config import CONFIG
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import HelperTaskDto, HelperTaskType

#
# General
#


def wrap_email_html(content: str) -> str:
    # Wrap the content in a table to ensure it is displayed correctly in the most email clients
    return f"""
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
        <td>{content}</td>
    </tr>
</table>
</body>
</html>
"""


#
# Date Format
#


def format_date(date: datetime | None) -> str | None:
    return date.strftime("%d/%m/%Y") if date else None


def format_date_with_day(date: datetime | None) -> str | None:
    #
    return date.strftime("%A, %d %B %Y") if date else None


def format_time(date: datetime | None) -> str | None:
    # Example: 12:00
    return date.strftime("%H:%M") if date else None


def format_date_time(date: datetime | None) -> str | None:
    # Example: 01/01/2022 12:00
    return date.strftime("%d/%m/%Y, %H:%M") if date else None


#
# Email Format
#


def format_email_link(email: str) -> str:
    return f'<a href="mailto:{email}">{email}</a>'


#
# Phone Format
#


def format_phone(phone: str | None) -> str | None:
    if not phone:
        return None

    try:
        if phone.startswith("00"):
            phone = phone.replace("00", "+", 1)

        return phonenumbers.format_number(
            phonenumbers.parse(phone), phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
    except phonenumbers.phonenumberutil.NumberParseException:
        return phone


def format_phone_link(phone: str | None) -> str | None:
    if not phone:
        return None

    formatted_phone = format_phone(phone)
    return f'<a href="tel:{phone}">{formatted_phone}</a>'


def format_phone_links(member: MemberPublicInfoDto) -> str | None:
    phones = []
    if member.mobile_phone:
        phones.append(f"Mobile: {format_phone_link(member.mobile_phone)}")
    if member.home_phone:
        phones.append(f"Home: {format_phone_link(member.home_phone)}")
    if member.work_phone:
        phones.append(f"Work: {format_phone_link(member.work_phone)}")

    # Theoretically it is possible that in the DB all phone numbers are missing
    return " / ".join(phones) if phones else None


#
# Member Format
#


def format_member_info(member: MemberPublicInfoDto) -> str:
    member_info = (
        f"{member.full_name} ({member.username}): {format_email_link(member.email)}"
    )

    phones = format_phone_links(member)
    if phones:
        member_info += f" / {phones}"
    return member_info


#
# Task Format
#

SHIFT_REPLACEMENT_REMINDER = """
<p>
    <em>Reminder: If you cannot help with a task any more, we kindly ask you to find a replacement
    (e.g., during an outing or in one of the YCC WhatsApp groups) and let us know.</em>
</p>
"""

YCC_APP_SIGNATURE = """
<p>
    Kind wishes,<br />
    YCC Maintenance & Regatta & Surveillance Teams
</p>
"""


def _get_helper_task_url(task: HelperTaskDto) -> str:
    return f"{CONFIG.ycc_app.base_url}/helpers/tasks/{task.id}"


def format_helper_task_timing(task: HelperTaskDto) -> str:
    # Note: Also used in email subjects as plain text
    if task.type == HelperTaskType.SHIFT:
        same_day_end = (
            task.starts_at
            and task.ends_at
            and task.starts_at.date() == task.ends_at.date()
        )
        if same_day_end:
            return f"Shift: {format_date_with_day(task.starts_at)} {format_time(task.starts_at)} &ndash; {format_time(task.ends_at)}"
        else:
            return f"Multi-Day Shift: {format_date_time(task.starts_at)} &ndash; {format_date_time(task.ends_at)}"
    elif task.type == HelperTaskType.DEADLINE:
        return f"Deadline: {format_date_with_day(task.deadline)} {format_time(task.deadline)}"
    else:
        return f"Start: {format_date_time(task.starts_at)} End: {format_date_time(task.ends_at)} Deadline: {format_date_time(task.deadline)}"


def format_helper_task_subject(task: HelperTaskDto) -> str:
    return f"{task.title} ({format_helper_task_timing(task).replace('&ndash;', '-')})"


def format_helper_task(task: HelperTaskDto) -> str:
    task_url = _get_helper_task_url(task)

    helpers = []
    if task.helpers:
        helpers.append("<ul>")

        for helper in task.helpers:
            helpers.append(f"  <li>{format_member_info(helper.member)}</li>")

        helpers.append("</ul>")
    else:
        helpers.append("-")

    return f"""
<div>
    <p style="font-size: x-large;">
        <strong>{task.title} ({task.category.title})</strong>
    </p>
    <p style="font-size: large;"><strong>{format_helper_task_timing(task)}</strong></p>
    <p><em>{task.short_description}</em></p>
    <ul>
        <li>Contact: {format_member_info(task.contact)}</li>
        <li>Captain: {format_member_info(task.captain.member) if task.captain else "-"}</li>
        <li>Helpers: {"".join(helpers)}</li>
    </ul>
    <p>
        <a
            href="{task_url}"
            style="
                display: inline-block;
                padding: 6px 16px;
                font-size: large;
                color: #ffffff;
                background-color: #1976d2;
                text-decoration: none;
                border-radius: 4px;
            "
        >
            <strong>Open in the YCC App</strong>
        </a>
    </p>
</div>
"""
