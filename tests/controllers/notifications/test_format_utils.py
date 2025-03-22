"""
Notifications format utils test.
"""

from datetime import datetime

import pytest

from ycc_hull.controllers.notifications.format_utils import (
    format_date,
    format_date_time,
    format_date_with_day,
    format_phone,
    format_time,
)

#
# Date Format
#


@pytest.mark.parametrize(
    "input_date, expected",
    [
        (None, None),
        (datetime(2025, 1, 1), "01/01/2025"),
        (datetime(2025, 12, 31), "31/12/2025"),
        (datetime(2024, 2, 29), "29/02/2024"),
    ],
)
def test_format_date(input_date: datetime | None, expected: str | None) -> None:
    assert format_date(input_date) == expected


@pytest.mark.parametrize(
    "input_date, expected",
    [
        (None, None),
        (datetime(2025, 1, 1), "Wednesday, 1 January 2025"),
        (datetime(2024, 2, 29), "Thursday, 29 February 2024"),
        (datetime(2025, 12, 31), "Wednesday, 31 December 2025"),
    ],
)
def test_format_date_with_day(
    input_date: datetime | None, expected: str | None
) -> None:
    assert format_date_with_day(input_date) == expected


@pytest.mark.parametrize(
    "input_date, expected",
    [
        (None, None),
        (datetime(2025, 1, 1, 0, 0), "00:00"),
        (datetime(2025, 1, 1, 9, 5), "09:05"),
        (datetime(2025, 1, 1, 12, 0), "12:00"),
        (datetime(2025, 1, 1, 23, 59), "23:59"),
    ],
)
def test_format_time(input_date: datetime | None, expected: str | None) -> None:
    assert format_time(input_date) == expected


@pytest.mark.parametrize(
    "input_date, expected",
    [
        (None, None),
        (datetime(2025, 1, 1, 0, 0), "01/01/2025 00:00"),
        (datetime(2024, 2, 29, 9, 5), "29/02/2024 09:05"),
        (datetime(2025, 12, 31, 23, 59), "31/12/2025 23:59"),
    ],
)
def test_format_date_time(input_date: datetime | None, expected: str | None) -> None:
    assert format_date_time(input_date) == expected


#
# Phone Format
#


@pytest.mark.parametrize(
    "input_phone, expected",
    [
        (None, None),
        ("", None),
        ("+41761234567", "+41 76 123 45 67"),
        ("0041761234567", "+41 76 123 45 67"),
        ("+33761234567", "+33 7 61 23 45 67"),
        ("0033761234567", "+33 7 61 23 45 67"),
        ("+36301234567", "+36 30 123 4567"),
        ("0036301234567", "+36 30 123 4567"),
        ("0761234567", "0761234567"),
        ("some random string", "some random string"),
    ],
)
def test_format_phone(input_phone: str | None, expected: str | None) -> None:
    assert format_phone(input_phone) == expected
