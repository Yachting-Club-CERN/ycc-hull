"""Tests for EmailMessageBuilder."""

import pytest

from tests.factories import make_member, make_user
from ycc_hull.controllers.notifications.email_message_builder import EmailMessageBuilder


def _valid_builder() -> EmailMessageBuilder:
    return (
        EmailMessageBuilder()
        .from_("sender@example.com")
        .to("recipient@example.com")
        .subject("Test subject")
        .content("<p>Hello</p>")
    )


# ==============================================================================
# _extract_address
# ==============================================================================


def test_extract_address_from_string() -> None:
    builder = _valid_builder()
    assert (
        builder._extract_address("test@example.com")  # noqa: SLF001
        == "test@example.com"
    )


def test_extract_address_from_user() -> None:
    builder = _valid_builder()
    addr = builder._extract_address(  # noqa: SLF001
        make_user(
            username="alice",
            email="alice@example.com",
            first_name="Alice",
            last_name="Smith",
        )
    )
    assert addr == "Alice Smith <alice@example.com>"


def test_extract_address_from_member_dto() -> None:
    builder = _valid_builder()
    addr = builder._extract_address(  # noqa: SLF001
        make_member(
            member_id=2,
            username="bob",
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
        )
    )
    assert addr == "Bob Jones <bob@example.com>"


def test_extract_address_unsupported_type() -> None:
    builder = _valid_builder()
    with pytest.raises(
        TypeError,
        match=r"^Expected string, MemberPublicInfoDto or User, got 12345$",
    ):
        builder._extract_address(12345)  # type: ignore[arg-type]  # noqa: SLF001


# ==============================================================================
# build validations
# ==============================================================================


def test_build_fails_without_to() -> None:
    builder = (
        EmailMessageBuilder()
        .from_("sender@example.com")
        .subject("Test")
        .content("<p>Hi</p>")
    )
    with pytest.raises(RuntimeError, match=r"^Recipient \(TO\) is not set$"):
        builder.build()


def test_build_fails_without_subject() -> None:
    builder = (
        EmailMessageBuilder()
        .from_("sender@example.com")
        .to("recipient@example.com")
        .content("<p>Hi</p>")
    )
    with pytest.raises(RuntimeError, match=r"^Subject is not set$"):
        builder.build()


def test_build_fails_without_content() -> None:
    builder = (
        EmailMessageBuilder()
        .from_("sender@example.com")
        .to("recipient@example.com")
        .subject("Test")
    )
    with pytest.raises(RuntimeError, match=r"^Content is not set$"):
        builder.build()


# ==============================================================================
# build success
# ==============================================================================


def test_build_basic_email() -> None:
    msg = _valid_builder().build()

    assert msg["From"] == "sender@example.com"
    assert msg["To"] == "recipient@example.com"
    assert msg["Subject"] == "Test subject"
    assert msg["Cc"] is None


def test_build_with_reply_to() -> None:
    msg = _valid_builder().reply_to("reply@example.com").build()

    assert msg["Reply-To"] == "reply@example.com"


def test_build_with_cc() -> None:
    msg = _valid_builder().cc("cc@example.com").build()

    assert msg["Cc"] == "cc@example.com"


def test_build_cc_deduplicates_with_to() -> None:
    """CC recipients already in TO should be removed."""
    msg = _valid_builder().cc("recipient@example.com").build()  # same as TO

    assert msg["Cc"] is None


def test_build_with_iterable_contacts() -> None:
    msg = (
        EmailMessageBuilder()
        .from_("sender@example.com")
        .to(["a@example.com", "b@example.com"])
        .subject("Test")
        .content("<p>Hi</p>")
        .build()
    )

    assert set(msg["To"].split(", ")) == {"a@example.com", "b@example.com"}


def test_build_with_iterable_skips_none() -> None:
    msg = (
        EmailMessageBuilder()
        .from_("sender@example.com")
        .to(["a@example.com", None])
        .subject("Test")
        .content("<p>Hi</p>")
        .build()
    )

    assert msg["To"] == "a@example.com"


def test_to_with_none_is_noop() -> None:
    builder = _valid_builder().to(None)
    msg = builder.build()
    assert msg["To"] == "recipient@example.com"
