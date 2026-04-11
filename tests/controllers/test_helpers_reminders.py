from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import getaddresses
from unittest.mock import MagicMock

import pytest
import pytest_asyncio

from tests.mock_utils import patch_reminders
from tests.test_main import app_test, init_test_database
from ycc_hull.app_controllers import get_controllers
from ycc_hull.controllers.helpers_controller import HelpersController
from ycc_hull.db.context import DatabaseContextHolder
from ycc_hull.db.entities import HelperTaskEntity
from ycc_hull.utils import TIME_ZONE

# Use a fixed tz-aware "now" to make tests deterministic.
NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=TIME_ZONE)
TODAY_START = NOW.replace(hour=0, minute=0, second=0, microsecond=0)

# Test data contact: member_id=1 is "Michele Huff" (from test_data/utils/members)
CONTACT_EMAIL = "michele.huff@mailinator.com"
CONTACT_NAME = "Michele Huff"
CONTACT_TO = f"{CONTACT_NAME} <{CONTACT_EMAIL}>"

# Email sender configured in tests
FROM_EMAIL = "noreply@test.ycc.fr"
APP_NAME = "YCC Hull Test"
FROM_ADDR = f"{APP_NAME} <{FROM_EMAIL}>"


@pytest_asyncio.fixture(scope="module", autouse=True)
async def init_database():
    await init_test_database(__name__)


def _controller() -> HelpersController:
    return get_controllers(app_test).helpers_controller


def _insert_task(  # noqa: PLR0913
    *,
    task_id: int,
    contact_id: int = 1,
    category_id: int = 2,
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    deadline: datetime | None = None,
    validated_by_id: int | None = None,
    published: bool = True,
) -> None:
    with DatabaseContextHolder.context.session() as session:
        session.add(
            HelperTaskEntity(
                id=task_id,
                category_id=category_id,
                title=f"Test Task {task_id}",
                short_description="Test task for reminders",
                contact_id=contact_id,
                starts_at=starts_at,
                ends_at=ends_at,
                deadline=deadline,
                helper_min_count=1,
                helper_max_count=2,
                urgent=False,
                published=published,
                validated_by_id=validated_by_id,
            )
        )
        session.commit()


def _delete_task(task_id: int) -> None:
    with DatabaseContextHolder.context.session() as session:
        task = session.get(HelperTaskEntity, task_id)
        if task:
            session.delete(task)
            session.commit()


def _get_sent_emails(mock_smtp: MagicMock) -> list[EmailMessage]:
    return [call.args[0] for call in mock_smtp.send_message.call_args_list]


def _to_emails(msg: EmailMessage) -> set[str]:
    raw = msg["To"]
    if not raw:
        return set()
    return {addr for _, addr in getaddresses([raw])}


async def _run_reminders() -> list[EmailMessage]:
    with patch_reminders(now=NOW, from_email=FROM_EMAIL, app_name=APP_NAME) as smtp:
        await _controller().send_daily_reminders()
    return _get_sent_emails(smtp)


def _find_email_by_task_title(
    emails: list[EmailMessage], task_id: int
) -> EmailMessage | None:
    title = f"Test Task {task_id}"
    for email in emails:
        if title in (email["Subject"] or ""):
            return email
    return None


def _find_overdue_emails(emails: list[EmailMessage]) -> list[EmailMessage]:
    return [e for e in emails if "overdue" in (e["Subject"] or "").lower()]


def _find_contact_overdue_email(
    emails: list[EmailMessage], contact_email: str
) -> EmailMessage:
    overdue = _find_overdue_emails(emails)
    matches = [e for e in overdue if contact_email in _to_emails(e)]
    assert len(matches) == 1, (
        f"Expected exactly 1 overdue email to {contact_email}, "
        f"got {len(matches)} (out of {len(overdue)} total overdue)"
    )
    return matches[0]


def _assert_email_not_mentioned(emails: list[EmailMessage], task_id: int) -> None:
    title = f"Test Task {task_id}"
    for email in emails:
        assert title not in (email["Subject"] or ""), (
            f"Task {task_id} should not appear in subject: {email['Subject']}"
        )
        assert title not in email.get_content(), (
            f"Task {task_id} should not appear in body"
        )


# ==============================================================================
# Emails disabled
# ==============================================================================


@pytest.mark.asyncio
async def test_emails_disabled_sends_no_emails():
    with patch_reminders(now=NOW, emails_enabled=False) as smtp:
        await _controller().send_daily_reminders()

    smtp.send_message.assert_not_called()


# ==============================================================================
# Upcoming reminders
# ==============================================================================


@pytest.mark.asyncio
async def test_upcoming_shift_due_in_14_days():
    task_id = 9001
    starts_at = TODAY_START + timedelta(days=14, hours=18)
    ends_at = starts_at + timedelta(hours=2)
    _insert_task(task_id=task_id, starts_at=starts_at, ends_at=ends_at)
    try:
        emails = await _run_reminders()

        email = _find_email_by_task_title(emails, task_id)
        assert email is not None, f"Expected upcoming reminder email for task {task_id}"

        assert email["From"] == FROM_ADDR
        assert CONTACT_EMAIL in _to_emails(email)
        assert email["Reply-To"] == CONTACT_TO

        subject = email["Subject"]
        assert f"Test Task {task_id}" in subject
        assert "Shift:" in subject
        assert "29 June 2026" in subject

        body = email.get_content()
        assert "quick reminder about your upcoming task" in body
        assert f"Test Task {task_id}" in body
        assert "No captain has signed up." in body
        assert "No helpers have signed up" in body
    finally:
        _delete_task(task_id)


@pytest.mark.asyncio
async def test_upcoming_shift_due_in_3_days():
    task_id = 9002
    starts_at = TODAY_START + timedelta(days=3, hours=18)
    ends_at = starts_at + timedelta(hours=2)
    _insert_task(task_id=task_id, starts_at=starts_at, ends_at=ends_at)
    try:
        emails = await _run_reminders()

        email = _find_email_by_task_title(emails, task_id)
        assert email is not None, f"Expected upcoming reminder email for task {task_id}"

        assert email["From"] == FROM_ADDR
        assert CONTACT_EMAIL in _to_emails(email)

        subject = email["Subject"]
        assert f"Test Task {task_id}" in subject
        assert "Shift:" in subject
        assert "18 June 2026" in subject

        body = email.get_content()
        assert "quick reminder about your upcoming task" in body
        assert f"Test Task {task_id}" in body
    finally:
        _delete_task(task_id)


@pytest.mark.asyncio
async def test_upcoming_shift_due_today():
    task_id = 9003
    starts_at = NOW + timedelta(hours=4)
    ends_at = starts_at + timedelta(hours=2)
    _insert_task(task_id=task_id, starts_at=starts_at, ends_at=ends_at)
    try:
        emails = await _run_reminders()

        email = _find_email_by_task_title(emails, task_id)
        assert email is not None, f"Expected upcoming reminder email for task {task_id}"

        assert email["From"] == FROM_ADDR
        assert CONTACT_EMAIL in _to_emails(email)

        subject = email["Subject"]
        assert f"Test Task {task_id}" in subject
        assert "15 June 2026" in subject

        body = email.get_content()
        assert "quick reminder about your upcoming task" in body
    finally:
        _delete_task(task_id)


@pytest.mark.asyncio
async def test_upcoming_deadline_task_due_in_3_days():
    task_id = 9004
    deadline = TODAY_START + timedelta(days=3, hours=20)
    _insert_task(task_id=task_id, deadline=deadline)
    try:
        emails = await _run_reminders()

        email = _find_email_by_task_title(emails, task_id)
        assert email is not None, f"Expected upcoming reminder email for task {task_id}"

        assert email["From"] == FROM_ADDR
        assert CONTACT_EMAIL in _to_emails(email)

        subject = email["Subject"]
        assert f"Test Task {task_id}" in subject
        assert "Deadline:" in subject
        assert "18 June 2026" in subject

        body = email.get_content()
        assert "quick reminder about your upcoming task" in body
        assert "No captain has signed up." in body
    finally:
        _delete_task(task_id)


# ==============================================================================
# Skipped tasks (no email sent)
# ==============================================================================


@pytest.mark.asyncio
async def test_ongoing_task_no_email():
    task_id = 9010
    starts_at = NOW - timedelta(hours=1)
    ends_at = NOW + timedelta(hours=1)
    _insert_task(task_id=task_id, starts_at=starts_at, ends_at=ends_at)
    try:
        emails = await _run_reminders()
        _assert_email_not_mentioned(emails, task_id)
    finally:
        _delete_task(task_id)


@pytest.mark.asyncio
async def test_validated_task_no_email():
    task_id = 9011
    starts_at = NOW - timedelta(days=10)
    ends_at = starts_at + timedelta(hours=2)
    _insert_task(
        task_id=task_id,
        starts_at=starts_at,
        ends_at=ends_at,
        validated_by_id=1,
    )
    try:
        emails = await _run_reminders()
        _assert_email_not_mentioned(emails, task_id)
    finally:
        _delete_task(task_id)


@pytest.mark.asyncio
async def test_task_not_in_reminder_window_no_email():
    task_id = 9013
    starts_at = TODAY_START + timedelta(days=7, hours=18)
    ends_at = starts_at + timedelta(hours=2)
    _insert_task(task_id=task_id, starts_at=starts_at, ends_at=ends_at)
    try:
        emails = await _run_reminders()
        _assert_email_not_mentioned(emails, task_id)
    finally:
        _delete_task(task_id)


# ==============================================================================
# Overdue reminders
# ==============================================================================


@pytest.mark.asyncio
async def test_overdue_deadline_task_sends_grouped_email():
    task_id = 9020
    deadline = NOW - timedelta(days=2)
    _insert_task(task_id=task_id, deadline=deadline)
    try:
        emails = await _run_reminders()

        overdue_emails = _find_overdue_emails(emails)

        # Find the one addressed to our contact
        contact_overdue = [e for e in overdue_emails if CONTACT_EMAIL in _to_emails(e)]
        assert len(contact_overdue) == 1

        email = contact_overdue[0]
        assert email["From"] == FROM_ADDR
        assert email["To"] == CONTACT_TO
        assert email["Reply-To"] == CONTACT_TO

        subject = email["Subject"]
        assert "overdue task" in subject.lower()

        body = email.get_content()
        assert f"Test Task {task_id}" in body
        assert "you are the contact for" in body
        assert "overdue" in body.lower()
    finally:
        _delete_task(task_id)


@pytest.mark.asyncio
async def test_overdue_shift_past_grace_period_sends_email():
    task_id = 9021
    starts_at = NOW - timedelta(days=10)
    ends_at = starts_at + timedelta(hours=2)
    _insert_task(
        task_id=task_id,
        starts_at=starts_at,
        ends_at=ends_at,
        category_id=1,
    )
    try:
        emails = await _run_reminders()

        email = _find_contact_overdue_email(emails, CONTACT_EMAIL)
        assert f"Test Task {task_id}" in email.get_content()
    finally:
        _delete_task(task_id)


@pytest.mark.asyncio
async def test_overdue_shift_in_grace_period_no_email():
    task_id = 9022
    starts_at = NOW - timedelta(days=3)
    ends_at = starts_at + timedelta(hours=2)
    _insert_task(
        task_id=task_id,
        starts_at=starts_at,
        ends_at=ends_at,
        category_id=1,
    )
    try:
        emails = await _run_reminders()
        _assert_email_not_mentioned(emails, task_id)
    finally:
        _delete_task(task_id)


# ==============================================================================
# Edge cases / boundaries
# ==============================================================================


@pytest.mark.asyncio
async def test_shift_grace_period_boundary_exactly_7_days():
    task_id = 9030
    ends_at = NOW - timedelta(days=7)
    starts_at = ends_at - timedelta(hours=2)
    _insert_task(
        task_id=task_id,
        starts_at=starts_at,
        ends_at=ends_at,
        category_id=1,
    )
    try:
        emails = await _run_reminders()

        email = _find_contact_overdue_email(emails, CONTACT_EMAIL)
        assert f"Test Task {task_id}" in email.get_content()
    finally:
        _delete_task(task_id)


@pytest.mark.asyncio
async def test_unpublished_task_still_sends_email():
    task_id = 9031
    deadline = NOW - timedelta(days=2)
    _insert_task(task_id=task_id, deadline=deadline, published=False)
    try:
        emails = await _run_reminders()

        email = _find_contact_overdue_email(emails, CONTACT_EMAIL)
        assert f"Test Task {task_id}" in email.get_content()
    finally:
        _delete_task(task_id)


@pytest.mark.asyncio
async def test_previous_year_unvalidated_task_sends_email():
    task_id = 9032
    deadline = datetime(2025, 12, 31, 20, 0, tzinfo=TIME_ZONE)
    _insert_task(task_id=task_id, deadline=deadline)
    try:
        emails = await _run_reminders()

        email = _find_contact_overdue_email(emails, CONTACT_EMAIL)
        assert f"Test Task {task_id}" in email.get_content()
    finally:
        _delete_task(task_id)
