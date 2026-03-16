"""General utilities."""

from datetime import datetime
from typing import Any, TypedDict
from zoneinfo import ZoneInfo

import humps
from pydantic import BaseModel

from ycc_hull.constants import TIME_ZONE_ID

TIME_ZONE = ZoneInfo(TIME_ZONE_ID)


def full_type_name(cls: type) -> str:
    """Return the fully qualified type name."""
    module = cls.__module__
    if module == "builtins":
        return cls.__qualname__
    return f"{module}.{cls.__qualname__}"


def short_type_name(cls: type) -> str:
    """Return the short type name."""
    return cls.__qualname__


def get_now() -> datetime:
    """Get the current time with time zone information.

    Returns:
        datetime: The current time.

    """
    return datetime.now(tz=TIME_ZONE)


def camel_case_to_words(string: str) -> str:
    """Convert a camelCase string into a space-separated lowercase string.

    Also replaces dots (.) with spaces to support dotted paths.

    Examples:
        >>> camel_case_to_words("myFieldName")
        'my field name'

        >>> camel_case_to_words("user.addressZipCode")
        'user address zip code'

        >>> camel_case_to_words("MyHTTPServerConfig.someID")
        'my http server config some id'

    Args:
        string (str): The camelCase or PascalCase string (optionally with dots).

    Returns:
        str: A human-readable, space-separated version of the input.

    """
    return (
        humps.decamelize(string.replace(" ", "_")).replace("_", " ").replace(".", " ")
    )


class DiffEntry(TypedDict):
    """Represents a difference between two values."""

    old: Any
    new: Any


def _deep_diff_values(
    v1: Any,  # noqa: ANN401
    v2: Any,  # noqa: ANN401
    diff: dict[str, DiffEntry],
    path: str,
) -> None:
    if isinstance(v1, dict) and isinstance(v2, dict):
        _deep_diff(v1, v2, diff, f"{path}.")
    elif isinstance(v1, list) and isinstance(v2, list):
        for i in range(max(len(v1), len(v2))):
            elem1 = v1[i] if i < len(v1) else None
            elem2 = v2[i] if i < len(v2) else None
            _deep_diff_values(elem1, elem2, diff, f"{path}.{i}")
    elif v1 != v2:
        diff[path] = {"old": v1, "new": v2}


def _deep_diff(
    d1: dict,
    d2: dict,
    diff: dict[str, DiffEntry],
    prefix: str = "",
) -> None:

    keys = set(d1.keys()).union(d2.keys())
    for key in keys:
        path = f"{prefix}{key}"

        v1 = d1.get(key)
        v2 = d2.get(key)

        _deep_diff_values(v1, v2, diff, path)


def deep_diff(d1: dict | BaseModel, d2: dict | BaseModel) -> dict[str, DiffEntry]:
    """Compute a deep diff between two dictionaries or Pydantic objects.

    Keys that are missing in one dictionary are treated as having the value `None`.
    As a result, a key explicitly set to `None` is considered equal to a missing key.
    (This is good enough as the main use of this function is to compare dictionaries of
    the same structure.)

    Args:
        d1 (dict): The first dictionary.
        d2 (dict): The second dictionary.

    Returns:
        dict: The diff between the two dictionaries.

    """
    if isinstance(d1, BaseModel):
        d1 = d1.model_dump(by_alias=True)
    if isinstance(d2, BaseModel):
        d2 = d2.model_dump(by_alias=True)

    diff: dict[str, DiffEntry] = {}
    _deep_diff(d1, d2, diff)
    return diff
