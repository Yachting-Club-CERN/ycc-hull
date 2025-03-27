"""
Utility functions for formatting email content.

We could use Jinja2, but we would still need to implement most helpers in Python, so sticking to plain Python formatting makes things simpler.
"""

import sys
from datetime import datetime
from typing import Iterable

import phonenumbers

from ycc_hull.config import CONFIG
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import HelperTaskDto, HelperTaskType

#
# General
#


def wrap_email_html(content: str) -> str:
    """
    Wraps the given content in a table layout to improve compatibility across different email clients.
    """
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
    # Example: 01/01/2025
    return date.strftime("%d/%m/%Y") if date else None


def format_date_with_day(date: datetime | None) -> str | None:
    # Example: Wednesday, 1 January 2025
    if not date:
        return None

    date_format = "%A, %#d %B %Y" if sys.platform == "win32" else "%A, %-d %B %Y"
    return date.strftime(date_format)


def format_time(date: datetime | None) -> str | None:
    # Example: 12:00
    return date.strftime("%H:%M") if date else None


def format_date_time(date: datetime | None) -> str | None:
    # Example: 01/01/2025, 12:00
    return date.strftime("%d/%m/%Y %H:%M") if date else None


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
    <em>Reminder 📢: If you cannot help with a task any more, we kindly ask you to find a replacement
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


def format_helper_task_timing_with_extra(task: HelperTaskDto) -> str:
    timing_extra = []
    if task.urgent:
        timing_extra.append("URGENT")
    if not task.published:
        timing_extra.append("HIDDEN")

    timing_extra_str = f" ({", ".join(timing_extra)})" if timing_extra else ""

    return f"{format_helper_task_timing(task)}{timing_extra_str}"


def format_helper_task_min_max_helpers(task: HelperTaskDto) -> str:
    if task.helper_min_count == task.helper_max_count:
        return f"{task.helper_min_count}"
    else:
        return f"{task.helper_min_count} - {task.helper_max_count}"


def format_helper_task_subject(task: HelperTaskDto) -> str:
    return (
        f"⛵🔔 {task.title} ({format_helper_task_timing(task).replace('&ndash;', '-')})"
    )


def format_helper_task(
    task: HelperTaskDto, *, warnings: list[str] | None = None
) -> str:
    task_url = _get_helper_task_url(task)

    warnings_html = (
        f"""
    <p style="color: #ff0000;">
        {"<br />\n".join(warning for warning in warnings)}
    </p>
"""
        if warnings
        else ""
    )

    if task.helpers:
        helpers_html = f"""
    <ul>
        {"\n".join(f"<li>{format_member_info(helper.member)}</li>" for helper in task.helpers)}
    </ul>
"""
    elif task.helper_min_count > 0:
        helpers_html = "😭"
    else:
        helpers_html = "Not needed"

    return f"""
<div>
    <p style="font-size: x-large;">
        <strong>{task.title} ({task.category.title})</strong>
    </p>
    <p style="font-size: large;"><strong>{format_helper_task_timing_with_extra(task)}</strong></p>
    {warnings_html}
    <p><em>{task.short_description}</em></p>
    <ul>
        <li>Contact: {format_member_info(task.contact)}</li>
        <li>Captain: {format_member_info(task.captain.member) if task.captain else "😭"}</li>
        <li>Helpers: {helpers_html}</li>
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
            <strong>Open in the App</strong>
        </a>
    </p>
</div>
"""


def format_helper_tasks_list(tasks: Iterable[HelperTaskDto]) -> str:
    def format_task_li(task: HelperTaskDto) -> str:
        task_url = _get_helper_task_url(task)

        return f"""
    <li>
        <a href="{task_url}">
            {task.title} ({format_helper_task_timing(task)})
        </a>
    </li>
"""

    return f"""
<ul>
    {"\n".join(format_task_li(task) for task in tasks)}
</ul>"""
