"""
General utilities.
"""

from datetime import datetime

import pytz

from ycc_hull.constants import TIME_ZONE_ID

TIME_ZONE = pytz.timezone(TIME_ZONE_ID)


def full_type_name(cls: type) -> str:
    module = cls.__module__
    if module == "builtins":
        return cls.__qualname__
    return f"{module}.{cls.__qualname__}"


def short_type_name(cls: type) -> str:
    return cls.__qualname__


def get_now() -> datetime:
    """Get the current time with time zone information.

    Returns:
        datetime: The current time.
    """
    return TIME_ZONE.localize(datetime.now())
