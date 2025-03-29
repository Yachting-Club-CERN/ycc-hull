"""Tests for the utils.camel_case_to_words"""

import pytest

from ycc_hull.utils import camel_case_to_words


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("simple", "simple"),
        ("aSimpleTest", "a simple test"),
        ("myFieldName", "my field name"),
        ("myNested.fieldName", "my nested field name"),
        ("HttpServerConfig.myId", "http server config my id"),
        ("HTTPServerConfig.myID", "http server config my id"),
        ("partly_formatted string", "partly formatted string"),
        ("", ""),
    ],
)
def test_camel_to_words(input_str: str, expected: str) -> None:
    assert camel_case_to_words(input_str) == expected
