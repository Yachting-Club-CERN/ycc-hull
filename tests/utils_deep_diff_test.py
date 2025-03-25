"""Tests for the utils.deep_diff"""

from ycc_hull.utils import deep_diff


def test_identical_dicts() -> None:
    d1 = {"a": 1, "b": {"x": 10}}
    d2 = {"a": 1, "b": {"x": 10}}
    assert len(deep_diff(d1, d2)) == 0


def test_simple_value_change() -> None:
    d1 = {"a": 1}
    d2 = {"a": 2}
    assert deep_diff(d1, d2) == {"a": {"old": 1, "new": 2}}


def test_nested_value_change() -> None:
    d1 = {"a": {"b": 1}}
    d2 = {"a": {"b": 2}}
    assert deep_diff(d1, d2) == {"a.b": {"old": 1, "new": 2}}


def test_key_added() -> None:
    d1 = {"a": 1}
    d2 = {"a": 1, "b": 2}
    assert deep_diff(d1, d2) == {"b": {"old": None, "new": 2}}


def test_key_removed() -> None:
    d1 = {"a": 1, "b": 2}
    d2 = {"a": 1}
    assert deep_diff(d1, d2) == {"b": {"old": 2, "new": None}}


def test_complex_nested_diff() -> None:
    d1 = {"a": 1, "b": {"a": 1, "b": None, "x": 10, "y": 20}, "c": None}
    d2 = {"a": 1, "b": {"a": 1, "c": None, "x": 15, "z": 25}, "d": 4, "e": None}
    assert deep_diff(d1, d2) == {
        "b.x": {"old": 10, "new": 15},
        "b.y": {"old": 20, "new": None},
        "b.z": {"old": None, "new": 25},
        "d": {"old": None, "new": 4},
    }


def test_type_mismatch() -> None:
    d1 = {"a": {"b": 1}}
    d2 = {"a": [1, 2]}
    assert deep_diff(d1, d2) == {"a": {"old": {"b": 1}, "new": [1, 2]}}
