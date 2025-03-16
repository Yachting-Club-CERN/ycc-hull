"""
Test data generator component for holidays.
"""

import json
from datetime import date, datetime

from test_data.generator_config import HOLIDAYS_EXPORTED_JSON_FILE
from ycc_hull.db.entities import HolidayEntity


def _parse_oracle_date(date_str: str) -> date:
    """
    Parses strings like "31-MAY-04" into dates.

    Args:
        date_str (str): Oracle DB date string

    Returns:
        date: date object
    """
    return datetime.strptime(date_str, "%d-%b-%y").date()


def generate_holidays() -> list[HolidayEntity]:
    with open(HOLIDAYS_EXPORTED_JSON_FILE, "r", encoding="utf-8") as file:
        return [
            HolidayEntity(
                day=_parse_oracle_date(holiday["day"]),
                label=holiday["label"],
                id=None if holiday["id"] == "" else holiday["id"],
            )
            for holiday in json.load(file)["results"][0]["items"]
        ]
