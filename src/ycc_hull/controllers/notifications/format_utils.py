"""Utility functions for formatting email content.

We could use Jinja2, but we would still need to implement most helpers in Python, so
sticking to plain Python formatting makes things simpler.
"""

import sys
from collections.abc import Iterable
from datetime import datetime

import phonenumbers

from ycc_hull.config import CONFIG
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import HelperTaskDto, HelperTaskType

#
# General
#


def wrap_email_html(content: str) -> str:
    """Wrap the given content in a table layout.

    This improves compatibility across different email clients.
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
    """Format a date."""
    # Example: 01/01/2025
    return date.strftime("%d/%m/%Y") if date else None


def format_date_with_day(date: datetime | None) -> str | None:
    """Format a date with day name."""
    # Example: Wednesday, 1 January 2025
    if not date:
        return None

    date_format = "%A, %#d %B %Y" if sys.platform == "win32" else "%A, %-d %B %Y"
    return date.strftime(date_format)


def format_time(date: datetime | None) -> str | None:
    """Format a time."""
    # Example: 12:00
    return date.strftime("%H:%M") if date else None


def format_date_time(date: datetime | None) -> str | None:
    """Format a date and time."""
    # Example: 01/01/2025, 12:00
    return date.strftime("%d/%m/%Y %H:%M") if date else None


#
# Email Format
#


def format_email_link(email: str) -> str:
    """Return an HTML mailto link for an email address."""
    return f'<a href="mailto:{email}">{email}</a>'


#
# Phone Format
#


def format_phone(phone: str | None) -> str | None:
    """Format a phone number internationally."""
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
    """Return an HTML tel link for a phone number."""
    if not phone:
        return None

    formatted_phone = format_phone(phone)
    return f'<a href="tel:{phone}">{formatted_phone}</a>'


def format_phone_links(member: MemberPublicInfoDto) -> str | None:
    """Return formatted phone links for a member."""
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
    """Format member name, username, email and phone."""
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


def _get_helper_task_url(task: HelperTaskDto) -> str:
    return f"{CONFIG.ycc_app.base_url}/helpers/tasks/{task.id}"


def format_helper_task_timing(task: HelperTaskDto) -> str:
    """Format the timing of a helper task as HTML."""
    # Note: Also used in email subjects as plain text
    if task.type == HelperTaskType.SHIFT:
        same_day_end = (
            task.starts_at
            and task.ends_at
            and task.starts_at.date() == task.ends_at.date()
        )
        if same_day_end:
            return (
                f"Shift: {format_date_with_day(task.starts_at)} "
                f"{format_time(task.starts_at)} &ndash; {format_time(task.ends_at)}"
            )
        return (
            f"Multi-Day Shift: {format_date_time(task.starts_at)} &ndash; "
            f"{format_date_time(task.ends_at)}"
        )
    if task.type == HelperTaskType.DEADLINE:
        return (
            f"Deadline: {format_date_with_day(task.deadline)} "
            f"{format_time(task.deadline)}"
        )
    return (
        f"Start: {format_date_time(task.starts_at)} "
        f"End: {format_date_time(task.ends_at)} "
        f"Deadline: {format_date_time(task.deadline)}"
    )


def format_helper_task_timing_with_extra(task: HelperTaskDto) -> str:
    """Format task timing with urgent/hidden flags."""
    timing_extra = []
    if task.urgent:
        timing_extra.append("URGENT")
    if not task.published:
        timing_extra.append("HIDDEN")

    timing_extra_str = f" ({', '.join(timing_extra)})" if timing_extra else ""

    return f"{format_helper_task_timing(task)}{timing_extra_str}"


def format_helper_task_min_max_helpers(task: HelperTaskDto) -> str:
    """Format the min/max helper count for a task."""
    if task.helper_min_count == task.helper_max_count:
        return f"{task.helper_min_count}"
    return f"{task.helper_min_count} - {task.helper_max_count}"


def format_helper_task_subject(task: HelperTaskDto) -> str:
    """Format the email subject line for a task."""
    return (
        f"⛵🔔 {task.title} ({format_helper_task_timing(task).replace('&ndash;', '-')})"
    )


def format_helper_task(
    task: HelperTaskDto, *, warnings: list[str] | None = None
) -> str:
    """Format a helper task as an HTML block."""
    task_url = _get_helper_task_url(task)

    warnings_html = (
        f"""
    <p style="color: #ff0000;">
        {"<br />\n".join(warnings)}
    </p>
"""
        if warnings
        else ""
    )

    if task.helpers:
        helpers_html = f"""
    <ul>
        {
            "\n".join(
                f"<li>{format_member_info(helper.member)}</li>"
                for helper in task.helpers
            )
        }
    </ul>
"""
    elif task.helper_min_count > 0:
        helpers_html = "-"
    else:
        helpers_html = "Not needed"

    timing = format_helper_task_timing_with_extra(task)
    contact = format_member_info(task.contact)
    captain = format_member_info(task.captain.member) if task.captain else "-"
    min_max = format_helper_task_min_max_helpers(task)

    return f"""
<div>
    <p style="font-size: x-large;">
        <strong>{task.title} ({task.category.title})</strong>
    </p>
    <p style="font-size: large;"><strong>{timing}</strong></p>
    {warnings_html}
    <p><em>{task.short_description}</em></p>
    <ul>
        <li>Contact: {contact}</li>
        <li>Captain: {captain}</li>
        <li>Helpers (needed: {min_max}): {helpers_html}</li>
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
    """Format a list of helper tasks as HTML."""

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
