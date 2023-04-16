"""
Helpers DTO tests.
"""
from pydantic import ValidationError
import pytest
from ycc_hull.models.helpers_dtos import HelperTaskCreationRequestDto


def test_creation_valid_shift() -> None:
    HelperTaskCreationRequestDto(
        category_id=1,
        title="Test Task",
        short_description="The Club needs your help!",
        contact_id=1,
        start="2023-05-01T18:00:00",
        end="2023-05-01T20:30:00",
        urgent=False,
        captain_required_licence_info_id=9,
        helpers_min_count=1,
        helpers_max_count=2,
        published=False,
    )


def test_creation_valid_deadline() -> None:
    HelperTaskCreationRequestDto(
        category_id=1,
        title="Test Task",
        short_description="The Club needs your help!",
        long_description="Really! It is very important to get this done!",
        contact_id=2,
        deadline="2023-05-02T20:00:00",
        urgent=True,
        helpers_min_count=2,
        helpers_max_count=2,
        published=True,
    )


def test_creation_must_specify_timing() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskCreationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            urgent=False,
            captain_required_licence_info_id=9,
            helpers_min_count=1,
            helpers_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid timing"


def test_creation_must_not_specify_all_timing_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskCreationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            start="2023-05-01T18:00:00",
            end="2023-05-01T20:30:00",
            deadline="2023-05-02T20:00:00",
            urgent=False,
            captain_required_licence_info_id=9,
            helpers_min_count=1,
            helpers_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid timing"


def test_creation_must_not_specify_start_with_deadline() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskCreationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            start="2023-05-01T18:00:00",
            deadline="2023-05-02T20:00:00",
            urgent=False,
            captain_required_licence_info_id=9,
            helpers_min_count=1,
            helpers_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid timing"


def test_creation_must_not_specify_end_with_deadline() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskCreationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            end="2023-05-01T20:30:00",
            deadline="2023-05-02T20:00:00",
            urgent=False,
            captain_required_licence_info_id=9,
            helpers_min_count=1,
            helpers_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid timing"


def test_creation_must_not_specify_start_after_end() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskCreationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            start="2023-05-01T20:30:00",
            end="2023-05-01T18:00:00",
            urgent=False,
            captain_required_licence_info_id=9,
            helpers_min_count=1,
            helpers_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid timing"


def test_creation_must_have_consistent_helper_counts() -> None:
    with pytest.raises(ValidationError) as exc_info:
        HelperTaskCreationRequestDto(
            category_id=1,
            title="Test Task",
            short_description="The Club needs your help!",
            contact_id=1,
            start="2023-05-01T18:00:00",
            end="2023-05-01T20:30:00",
            urgent=False,
            captain_required_licence_info_id=9,
            helpers_min_count=3,
            helpers_max_count=2,
            published=False,
        )

    assert exc_info.value.errors()[0]["msg"] == "Invalid minimum/maximum helper count"
