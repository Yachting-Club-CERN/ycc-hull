"""Utility functions for formatting email content."""

from datetime import datetime
from ycc_hull.config import CONFIG
from ycc_hull.models.dtos import MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import HelperTaskDto, HelperTaskType
import phonenumbers


def get_helper_task_url(task: HelperTaskDto) -> str:
    return f"{CONFIG.ycc_app.base_url}/helpers/tasks/{task.id}"


#
# Date Format
#


def format_date(date: datetime | None) -> str | None:
    return date.strftime("%d/%m/%Y") if date else None


def format_date_with_day(date: datetime | None) -> str | None:
    return date.strftime("%A, %d %B %Y") if date else None


def format_time(date: datetime | None) -> str | None:
    return date.strftime("%H:%M") if date else None


def format_date_time(date: datetime | None) -> str | None:
    return date.strftime("%d/%m/%Y, %H:%M") if date else None


#
# Email Format
#


def format_email(email: str) -> str:
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


def link_phone(phone: str | None) -> str | None:
    if not phone:
        return None

    formatted_phone = format_phone(phone)
    return f'<a href="tel:{phone}">{formatted_phone}</a>'


def link_phones(member: MemberPublicInfoDto) -> str | None:
    phones = []
    if member.mobile_phone:
        phones.append(f"Mobile: {link_phone(member.mobile_phone)}")
    if member.home_phone:
        phones.append(f"Home: {link_phone(member.home_phone)}")
    if member.work_phone:
        phones.append(f"Work: {link_phone(member.work_phone)}")

    # Theoretically it is possible that in the DB all phone numbers are missing
    return " / ".join(phones) if phones else None


def format_timing(task: HelperTaskDto) -> str:
    if task.type == HelperTaskType.SHIFT:
        same_day_end = task.starts_at.date() == task.ends_at.date()
        if same_day_end:
            return f"Shift: {format_date_with_day(task.starts_at)} {format_time(task.starts_at)} - {format_time(task.ends_at)}"
        else:
            return f"Multi-Day Shift: {format_date_time(task.starts_at)} - {format_date_time(task.ends_at)}"
    elif task.type == HelperTaskType.DEADLINE:
        return f"Deadline: {format_date_with_day(task.deadline)} {format_time(task.deadline)}"
    else:
        return f"Start: {format_date_time(task.starts_at)} End: {format_date_time(task.ends_at)} Deadline: {format_date_time(task.deadline)}"


#
# Member Format
#


def format_member_info(member: MemberPublicInfoDto) -> str:
    member_info = (
        f"{member.full_name} ({member.username}): {format_email(member.email)}"
    )
    phones = link_phones(member)
    if phones:
        member_info += f" / {phones}"
    return member_info
