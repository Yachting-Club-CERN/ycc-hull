"""
Helpers DTO tests.
"""
from datetime import datetime

import pytest
from pydantic import ValidationError

from ycc_hull.models.helpers_dtos import HelperTaskMutationRequestDto


def test_creation_valid_shift() -> None:
    request = HelperTaskMutationRequestDto(
        category_id=1,
        title="Test Task",
        short_description="The Club needs your help!",
        contact_id=1,
        starts_at="2023-05-01T18:00:00",
        ends_at="2023-05-01T20:30:00",
        urgent=False,
        captain_required_licence_info_id=9,
        helper_min_count=1,
        helper_max_count=2,
        published=False,
    )

    assert isinstance(request.starts_at, datetime)
    assert isinstance(request.ends_at, datetime)


def test_creation_valid_deadline() -> None:
    request = HelperTaskMutationRequestDto(
        category_id=1,
        title="Test Task",
        short_description="The Club needs your help!",
        long_description="Really! It is very important to get this done!",
        contact_id=2,
        deadline="2023-05-02T20:00:00",
        urgent=True,
        helper_min_count=2,
        helper_max_count=2,
        published=True,
    )

    assert isinstance(request.deadline, datetime)


def test_creation_must_specify_timing() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskMutationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            urgent=False,
            captain_required_licence_info_id=9,
            helper_min_count=1,
            helper_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid timing"


def test_creation_must_not_specify_all_timing_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskMutationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            starts_at="2023-05-01T18:00:00",
            ends_at="2023-05-01T20:30:00",
            deadline="2023-05-02T20:00:00",
            urgent=False,
            captain_required_licence_info_id=9,
            helper_min_count=1,
            helper_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid timing"


def test_creation_must_not_specify_start_with_deadline() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskMutationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            starts_at="2023-05-01T18:00:00",
            deadline="2023-05-02T20:00:00",
            urgent=False,
            captain_required_licence_info_id=9,
            helper_min_count=1,
            helper_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid timing"


def test_creation_must_not_specify_end_with_deadline() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskMutationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            ends_at="2023-05-01T20:30:00",
            deadline="2023-05-02T20:00:00",
            urgent=False,
            captain_required_licence_info_id=9,
            helper_min_count=1,
            helper_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid timing"


def test_creation_must_not_specify_start_after_end() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskMutationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            starts_at="2023-05-01T20:30:00",
            ends_at="2023-05-01T18:00:00",
            urgent=False,
            captain_required_licence_info_id=9,
            helper_min_count=1,
            helper_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid timing"


def test_creation_must_have_consistent_helper_counts() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskMutationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            starts_at="2023-05-01T18:00:00",
            ends_at="2023-05-01T20:30:00",
            urgent=False,
            captain_required_licence_info_id=9,
            helper_min_count=3,
            helper_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid minimum/maximum helper count"


def test_sanitise() -> None:
    request = HelperTaskMutationRequestDto(
        category_id=1,
        title="  <em>Test Task</em>  ",
        short_description="\t\nThe Club needs your help!\t<!-- Test -->\n",
        long_description=(
            "<em>Really!</em> It <notatag>is</notatag> very \nimportant "
            "<!-- Test -->to get this <script>alert('XSS')</script>done!<blink><p>Thank you!<p>\n"
            '<a href="http://example.com">Hyperlinks are OK</a>\n'
            '<img src="images-are-ok.jpg">\n'
            "<table>NO TABLES!</table> <form>NO FORMS!</form> <input> <button>NO BUTTONS!</button>\n"
            "<object>NO OBJECTS!</object> <embed>NO EMBEDS!</embed>\n"
            "<svg>NO SVGs!</svg> <canvas>NO CANVASES!</canvas>\n"
            "<head>NO HEADS!</head> <title>NO TITLES!</title>\n"
            "<base> <meta> <link> <style>NO STYLES!</style>\n"
        ),
        contact_id=1,
        starts_at="2023-05-01T18:00:00",
        ends_at="2023-05-01T20:30:00",
        urgent=False,
        captain_required_licence_info_id=9,
        helper_min_count=1,
        helper_max_count=2,
        published=False,
    )

    assert request.title == "Test Task"
    assert request.short_description == "The Club needs your help!"
    assert request.long_description == (
        "<div><em>Really!</em> It is very \nimportant to get this done!<p>Thank you!</p><p>\n"
        '<a href="http://example.com">Hyperlinks are OK</a>\n'
        '<img src="images-are-ok.jpg">\n'
        "</p>NO TABLES! NO FORMS!  \n \n \n"
        "NO HEADS! NO TITLES!\n   \n</div>"
    )
