"""Unit tests for HelpersNotificationsController.

These tests verify email construction and sending logic for each notification type.
SmtpConnection is mocked globally via conftest.py; here we use patch_notifications()
to control the enabled/disabled paths.
"""

from email.message import EmailMessage
from email.utils import getaddresses
from unittest.mock import AsyncMock, patch

import pytest

from tests.factories import make_helper, make_member, make_task_dto, make_user
from tests.mock_utils import patch_notifications, patch_notifications_with_sleep
from ycc_hull.controllers.notifications.format_utils import format_helper_task_subject
from ycc_hull.controllers.notifications.helpers_notifications_controller import (
    _SIGN_UP_MESSAGES,
    NOTIFICATION_DELAY_SECONDS,
    HelpersNotificationsController,
)
from ycc_hull.utils import DiffEntry

# ==============================================================================
# Email extraction helpers
# ==============================================================================


def _sent_message(send_mock: AsyncMock) -> EmailMessage:
    """Extract the EmailMessage from the first send_message call."""
    send_mock.assert_called_once()
    return send_mock.call_args[0][0]


def _to_emails(msg: EmailMessage) -> set[str]:
    """Extract To email addresses as a set."""
    raw = msg["To"]
    if not raw:
        return set()
    return {addr for _, addr in getaddresses([raw])}


def _cc_emails(msg: EmailMessage) -> set[str]:
    """Extract Cc email addresses as a set."""
    raw = msg["Cc"]
    if not raw:
        return set()
    return {addr for _, addr in getaddresses([raw])}


def _subject(msg: EmailMessage) -> str:
    """Extract the Subject header."""
    return msg["Subject"]


# ==============================================================================
# Emails disabled - all methods should early-return
# ==============================================================================


@pytest.mark.asyncio
async def test_emails_disabled_on_update_skipped() -> None:
    with patch_notifications(emails_enabled=False) as send:
        await HelpersNotificationsController().on_update(
            make_task_dto(), make_task_dto(), {}, make_user()
        )
        send.assert_not_called()


@pytest.mark.asyncio
async def test_emails_disabled_on_add_helper_skipped() -> None:
    with patch_notifications(emails_enabled=False) as send:
        await HelpersNotificationsController().on_add_helper(
            make_task_dto(), make_member(), make_user()
        )
        send.assert_not_called()


@pytest.mark.asyncio
async def test_emails_disabled_on_remove_helper_skipped() -> None:
    with patch_notifications(emails_enabled=False) as send:
        await HelpersNotificationsController().on_remove_helper(
            make_task_dto(), make_member(), make_user()
        )
        send.assert_not_called()


@pytest.mark.asyncio
async def test_emails_disabled_on_sign_up_skipped() -> None:
    with patch_notifications(emails_enabled=False) as send:
        await HelpersNotificationsController().on_sign_up(make_task_dto(), make_user())
        send.assert_not_called()


@pytest.mark.asyncio
async def test_emails_disabled_on_mark_as_done_skipped() -> None:
    with patch_notifications(emails_enabled=False) as send:
        await HelpersNotificationsController().on_mark_as_done(
            make_task_dto(), make_user()
        )
        send.assert_not_called()


@pytest.mark.asyncio
async def test_emails_disabled_on_validate_skipped() -> None:
    with patch_notifications(emails_enabled=False) as send:
        await HelpersNotificationsController().on_validate(make_task_dto(), make_user())
        send.assert_not_called()


@pytest.mark.asyncio
async def test_emails_disabled_send_reminders_skipped() -> None:
    with patch_notifications(emails_enabled=False) as send:
        await HelpersNotificationsController().send_reminders([], [])
        send.assert_not_called()


# ==============================================================================
# on_sign_up
# ==============================================================================


@pytest.mark.asyncio
async def test_sign_up_sends_email_to_user(mock_send_message: AsyncMock) -> None:
    user = make_user(email="bob@example.com")
    contact = make_member(
        member_id=10, first_name="Contact", email="contact@example.com"
    )
    task = make_task_dto(contact=contact)

    await HelpersNotificationsController().on_sign_up(task, user)

    msg = _sent_message(mock_send_message)
    assert _to_emails(msg) == {"bob@example.com"}
    assert _cc_emails(msg) == {"contact@example.com"}
    assert _subject(msg) == format_helper_task_subject(task)


@pytest.mark.asyncio
async def test_sign_up_content_contains_greeting_and_task(
    mock_send_message: AsyncMock,
) -> None:
    user = make_user(first_name="Bob")
    task = make_task_dto()

    with patch(
        "ycc_hull.controllers.notifications.helpers_notifications_controller"
        ".random.choice",
        return_value=_SIGN_UP_MESSAGES[0],
    ):
        await HelpersNotificationsController().on_sign_up(task, user)

    content = _sent_message(mock_send_message).get_content()
    assert "Dear Bob" in content
    assert "Thank you for signing up for this task!" in content
    assert task.title in content
    assert "find a replacement" in content
    assert "Fair Winds" in content


@pytest.mark.asyncio
async def test_sign_up_captain_cced_when_present(
    mock_send_message: AsyncMock,
) -> None:
    captain_member = make_member(member_id=77, email="cap@example.com")
    contact = make_member(member_id=10, email="contact@example.com")
    user = make_user(email="bob@example.com")
    task = make_task_dto(contact=contact, captain=make_helper(member=captain_member))

    await HelpersNotificationsController().on_sign_up(task, user)

    msg = _sent_message(mock_send_message)
    assert _to_emails(msg) == {"bob@example.com"}
    assert _cc_emails(msg) == {"contact@example.com", "cap@example.com"}


# ==============================================================================
# on_add_helper
# ==============================================================================


@pytest.mark.asyncio
async def test_add_helper_sends_to_helper(
    mock_send_message: AsyncMock,
) -> None:
    helper = make_member(member_id=20, email="new@example.com")
    task = make_task_dto()

    await HelpersNotificationsController().on_add_helper(task, helper, make_user())

    msg = _sent_message(mock_send_message)
    assert _to_emails(msg) == {"new@example.com"}
    assert _subject(msg) == format_helper_task_subject(task)


@pytest.mark.asyncio
async def test_add_helper_content_mentions_added(
    mock_send_message: AsyncMock,
) -> None:
    helper = make_member(member_id=20, first_name="NewHelper")
    user = make_user(first_name="Admin", last_name="Jones")

    await HelpersNotificationsController().on_add_helper(make_task_dto(), helper, user)

    content = _sent_message(mock_send_message).get_content()
    assert "Dear NewHelper" in content
    assert "Admin Jones has added you to this task." in content
    assert "find a replacement" in content
    assert "Fair Winds" in content


@pytest.mark.asyncio
async def test_add_helper_contact_and_captain_cced(
    mock_send_message: AsyncMock,
) -> None:
    contact = make_member(member_id=10, email="contact@example.com")
    captain_member = make_member(member_id=77, email="cap@example.com")
    user = make_user(email="admin@example.com")
    task = make_task_dto(contact=contact, captain=make_helper(member=captain_member))

    await HelpersNotificationsController().on_add_helper(
        task, make_member(member_id=20), user
    )

    cc = _cc_emails(_sent_message(mock_send_message))
    assert cc == {
        "contact@example.com",
        "cap@example.com",
        "admin@example.com",
    }


# ==============================================================================
# on_remove_helper
# ==============================================================================


@pytest.mark.asyncio
async def test_remove_helper_recipients_and_subject(
    mock_send_message: AsyncMock,
) -> None:
    helper = make_member(member_id=20, email="removed@example.com")
    contact = make_member(member_id=10, email="contact@example.com")
    user = make_user(email="admin@example.com")
    task = make_task_dto(contact=contact)

    await HelpersNotificationsController().on_remove_helper(task, helper, user)

    msg = _sent_message(mock_send_message)
    assert _to_emails(msg) == {"removed@example.com"}
    assert _cc_emails(msg) == {"contact@example.com", "admin@example.com"}
    assert _subject(msg) == format_helper_task_subject(task)


@pytest.mark.asyncio
async def test_remove_helper_content(
    mock_send_message: AsyncMock,
) -> None:
    helper = make_member(member_id=20, first_name="Removed")
    user = make_user(first_name="Admin", last_name="Jones")

    await HelpersNotificationsController().on_remove_helper(
        make_task_dto(), helper, user
    )

    content = _sent_message(mock_send_message).get_content()
    assert "Dear Removed" in content
    assert "Admin Jones has removed you from this task." in content
    assert "find a replacement" in content
    assert "Fair Winds" in content


@pytest.mark.asyncio
async def test_remove_helper_captain_cced_when_present(
    mock_send_message: AsyncMock,
) -> None:
    helper = make_member(member_id=20, email="removed@example.com")
    contact = make_member(member_id=10, email="contact@example.com")
    captain_member = make_member(member_id=77, email="cap@example.com")
    user = make_user(email="admin@example.com")
    task = make_task_dto(contact=contact, captain=make_helper(member=captain_member))

    await HelpersNotificationsController().on_remove_helper(task, helper, user)

    assert _cc_emails(_sent_message(mock_send_message)) == {
        "contact@example.com",
        "cap@example.com",
        "admin@example.com",
    }


# ==============================================================================
# on_mark_as_done
# ==============================================================================


@pytest.mark.asyncio
async def test_mark_as_done_recipients_and_subject(
    mock_send_message: AsyncMock,
) -> None:
    contact = make_member(member_id=10, email="contact@example.com")
    captain_member = make_member(member_id=77, email="cap@example.com")
    helper_member = make_member(member_id=50, email="helper@example.com")
    task = make_task_dto(
        contact=contact,
        captain=make_helper(member=captain_member),
        helpers=[make_helper(member=helper_member)],
    )
    user = make_user(email="marker@example.com")

    await HelpersNotificationsController().on_mark_as_done(task, user)

    msg = _sent_message(mock_send_message)
    assert _to_emails(msg) == {
        "contact@example.com",
        "cap@example.com",
        "helper@example.com",
    }
    assert _cc_emails(msg) == {"marker@example.com"}
    assert _subject(msg) == format_helper_task_subject(task)


@pytest.mark.asyncio
async def test_mark_as_done_content(
    mock_send_message: AsyncMock,
) -> None:
    user = make_user(first_name="Bob", last_name="Jones")
    contact = make_member(first_name="Contact", last_name="Person")

    await HelpersNotificationsController().on_mark_as_done(
        make_task_dto(contact=contact), user
    )

    content = _sent_message(mock_send_message).get_content()
    assert "Dear Sailors" in content
    assert "Bravo Zulu! Your help keeps the Club sailing smoothly!" in content
    assert (
        "Bob Jones has marked this task as done and it is now waiting for validation"
        "\nfrom Contact Person." in content
    )
    assert "Fair Winds" in content


# ==============================================================================
# on_validate
# ==============================================================================


@pytest.mark.asyncio
async def test_validate_recipients_and_subject(
    mock_send_message: AsyncMock,
) -> None:
    contact = make_member(member_id=10, email="contact@example.com")
    helper_member = make_member(member_id=50, email="helper@example.com")
    task = make_task_dto(contact=contact, helpers=[make_helper(member=helper_member)])
    user = make_user(email="validator@example.com")

    await HelpersNotificationsController().on_validate(task, user)

    msg = _sent_message(mock_send_message)
    assert _to_emails(msg) == {"contact@example.com", "helper@example.com"}
    assert _cc_emails(msg) == {"validator@example.com"}
    assert _subject(msg) == format_helper_task_subject(task)


@pytest.mark.asyncio
async def test_validate_content(
    mock_send_message: AsyncMock,
) -> None:
    user = make_user(first_name="Val", last_name="Idator")

    await HelpersNotificationsController().on_validate(make_task_dto(), user)

    content = _sent_message(mock_send_message).get_content()
    assert "Dear Sailors" in content
    assert "Bravo Zulu! Your help keeps the Club sailing smoothly!" in content
    assert "This task has been validated by Val Idator." in content


# ==============================================================================
# on_update
# ==============================================================================


@pytest.mark.asyncio
async def test_update_recipients_and_subject(
    mock_send_message: AsyncMock,
) -> None:
    contact = make_member(member_id=10, email="contact@example.com")
    helper_member = make_member(member_id=50, email="helper@example.com")
    task = make_task_dto(contact=contact, helpers=[make_helper(member=helper_member)])
    user = make_user(email="updater@example.com")

    await HelpersNotificationsController().on_update(task, task, {}, user)

    msg = _sent_message(mock_send_message)
    assert _to_emails(msg) == {"contact@example.com", "helper@example.com"}
    assert _cc_emails(msg) == {"updater@example.com"}
    assert _subject(msg) == format_helper_task_subject(task)


@pytest.mark.asyncio
async def test_update_no_changes_message(
    mock_send_message: AsyncMock,
) -> None:
    user = make_user(first_name="Updater", last_name="Person")
    task = make_task_dto()

    await HelpersNotificationsController().on_update(task, task, {}, user)

    content = _sent_message(mock_send_message).get_content()
    assert "Dear Sailors" in content
    assert "Updater Person has updated this task." in content
    assert (
        "Nothing seems to have changed"
        " \u2014 but it's still worth checking in the app!" in content
    )
    assert "find a replacement" in content


@pytest.mark.asyncio
async def test_update_with_title_change(
    mock_send_message: AsyncMock,
) -> None:
    diff: dict[str, DiffEntry] = {
        "title": {"old": "Old Title", "new": "New Title"},
    }

    await HelpersNotificationsController().on_update(
        make_task_dto(), make_task_dto(), diff, make_user()
    )

    content = _sent_message(mock_send_message).get_content()
    assert "Here is what changed: title." in content
    assert "Previous title" in content
    assert "Old Title" in content


@pytest.mark.asyncio
async def test_update_with_timing_change(
    mock_send_message: AsyncMock,
) -> None:
    diff: dict[str, DiffEntry] = {
        "startsAt": {"old": "10:00", "new": "11:00"},
    }

    await HelpersNotificationsController().on_update(
        make_task_dto(), make_task_dto(), diff, make_user()
    )

    content = _sent_message(mock_send_message).get_content()
    assert "Here is what changed: timing." in content
    assert "Previous timing" in content


@pytest.mark.asyncio
async def test_update_with_contact_change(
    mock_send_message: AsyncMock,
) -> None:
    diff: dict[str, DiffEntry] = {
        "contact.firstName": {"old": "OldContact", "new": "NewContact"},
    }

    await HelpersNotificationsController().on_update(
        make_task_dto(), make_task_dto(), diff, make_user()
    )

    content = _sent_message(mock_send_message).get_content()
    assert "Here is what changed: contact." in content
    assert "Previous contact" in content


@pytest.mark.asyncio
async def test_update_original_task_participants_also_notified(
    mock_send_message: AsyncMock,
) -> None:
    old_contact = make_member(member_id=10, email="old-contact@example.com")
    new_contact = make_member(member_id=11, email="new-contact@example.com")
    original = make_task_dto(contact=old_contact)
    updated = make_task_dto(contact=new_contact)
    user = make_user(email="updater@example.com")
    diff: dict[str, DiffEntry] = {
        "contact.email": {
            "old": "old-contact@example.com",
            "new": "new-contact@example.com",
        }
    }

    await HelpersNotificationsController().on_update(original, updated, diff, user)

    msg = _sent_message(mock_send_message)
    # Updated task's contact is in TO
    assert _to_emails(msg) == {"new-contact@example.com"}
    # Original contact and the updater are in CC
    assert _cc_emails(msg) == {"old-contact@example.com", "updater@example.com"}


# ==============================================================================
# send_reminders
# ==============================================================================


@pytest.mark.asyncio
async def test_reminders_sends_upcoming() -> None:
    task = make_task_dto()

    with patch_notifications_with_sleep() as (send, mock_sleep):
        await HelpersNotificationsController().send_reminders([task], [])

    send.assert_called_once()
    mock_sleep.assert_awaited_once_with(NOTIFICATION_DELAY_SECONDS)
    assert _subject(_sent_message(send)) == format_helper_task_subject(task)


@pytest.mark.asyncio
async def test_reminders_overdue_grouped_by_contact() -> None:
    contact_a = make_member(member_id=10, email="a@example.com")
    contact_b = make_member(member_id=20, email="b@example.com")
    task1 = make_task_dto(task_id=1, contact=contact_a)
    task2 = make_task_dto(task_id=2, contact=contact_a)
    task3 = make_task_dto(task_id=3, contact=contact_b)

    with patch_notifications_with_sleep() as (send, _mock_sleep):
        await HelpersNotificationsController().send_reminders([], [task1, task2, task3])

    # 2 overdue emails: one per contact
    assert send.call_count == 2


@pytest.mark.asyncio
async def test_reminders_overdue_mentions_task_count() -> None:
    contact = make_member(member_id=10, first_name="Charlie", email="c@example.com")
    tasks = [make_task_dto(task_id=i, contact=contact) for i in range(3)]

    with patch_notifications_with_sleep() as (send, _mock_sleep):
        await HelpersNotificationsController().send_reminders([], tasks)

    msg = _sent_message(send)
    content = msg.get_content()
    assert _to_emails(msg) == {"c@example.com"}
    assert _subject(msg) == "⛵⏰ 3 overdue tasks"
    assert "Dear Charlie" in content
    assert "you are the contact for 3 overdue tasks." in content


@pytest.mark.asyncio
async def test_reminders_overdue_single_task_no_plural() -> None:
    contact = make_member(member_id=10, first_name="Alice", email="a@example.com")
    task = make_task_dto(task_id=1, contact=contact)

    with patch_notifications_with_sleep() as (send, _mock_sleep):
        await HelpersNotificationsController().send_reminders([], [task])

    msg = _sent_message(send)
    content = msg.get_content()
    assert _subject(msg) == "⛵⏰ 1 overdue task"
    assert "you are the contact for 1 overdue task." in content
    assert "1 overdue tasks" not in content


@pytest.mark.asyncio
async def test_reminders_both_upcoming_and_overdue() -> None:
    upcoming = make_task_dto(task_id=1)
    overdue_contact = make_member(member_id=10)
    overdue = make_task_dto(task_id=2, contact=overdue_contact)

    with patch_notifications_with_sleep() as (send, mock_sleep):
        await HelpersNotificationsController().send_reminders([upcoming], [overdue])

    # 1 upcoming + 1 overdue
    assert send.call_count == 2
    assert mock_sleep.await_count == 2


@pytest.mark.asyncio
async def test_reminders_empty_lists_sends_nothing(
    mock_send_message: AsyncMock,
) -> None:
    await HelpersNotificationsController().send_reminders([], [])

    mock_send_message.assert_not_called()


@pytest.mark.asyncio
async def test_reminders_upcoming_with_warnings_includes_contact() -> None:
    """When a task has warnings, the contact is added to TO."""
    contact = make_member(member_id=10, email="contact@example.com")
    task = make_task_dto(contact=contact, captain=None, helpers=[], helper_min_count=2)

    with patch_notifications_with_sleep() as (send, _mock_sleep):
        await HelpersNotificationsController().send_reminders([task], [])

    msg = _sent_message(send)
    assert _to_emails(msg) == {"contact@example.com"}
    content = msg.get_content()
    assert "No captain has signed up." in content
    assert "No helpers have signed up" in content


@pytest.mark.asyncio
async def test_reminders_upcoming_without_warnings_no_contact_in_to() -> None:
    """When a task has no warnings, the contact is NOT in TO."""
    contact = make_member(member_id=10, email="contact@example.com")
    captain_member = make_member(member_id=77, email="cap@example.com")
    helper1 = make_helper(member=make_member(member_id=50, email="h1@example.com"))
    helper2 = make_helper(member=make_member(member_id=51, email="h2@example.com"))
    task = make_task_dto(
        contact=contact,
        captain=make_helper(member=captain_member),
        helpers=[helper1, helper2],
        helper_min_count=2,
    )

    with patch_notifications_with_sleep() as (send, _mock_sleep):
        await HelpersNotificationsController().send_reminders([task], [])

    msg = _sent_message(send)
    assert _to_emails(msg) == {
        "cap@example.com",
        "h1@example.com",
        "h2@example.com",
    }
    assert "contact@example.com" not in _to_emails(msg)


@pytest.mark.asyncio
async def test_reminders_upcoming_content() -> None:
    task = make_task_dto()

    with patch_notifications_with_sleep() as (send, _mock_sleep):
        await HelpersNotificationsController().send_reminders([task], [])

    content = _sent_message(send).get_content()
    assert "Dear Sailors" in content
    assert "This is just a quick reminder about your upcoming task." in content
    assert task.title in content


@pytest.mark.asyncio
async def test_reminders_overdue_content() -> None:
    contact = make_member(member_id=10, first_name="Contact", last_name="Person")
    task = make_task_dto(contact=contact)

    with patch_notifications_with_sleep() as (send, _mock_sleep):
        await HelpersNotificationsController().send_reminders([], [task])

    content = _sent_message(send).get_content()
    assert "Dear Contact" in content
    assert "you are the contact for 1 overdue task." in content
    assert "please validate it" in content
    assert "find a replacement" in content
