from tests.factories import make_helper, make_member, make_task_dto
from ycc_hull.controllers.notifications.format_utils import (
    format_helper_task_min_max_helpers,
    format_helper_task_timing,
    format_member_info,
)
from ycc_hull.controllers.notifications.helpers_notifications_controller import (
    _get_task_warnings,
    _HelperTaskChanges,
)
from ycc_hull.utils import DiffEntry

# ==============================================================================
# _get_task_warnings
# ==============================================================================


def test_get_task_warnings_no_warnings_when_fully_staffed() -> None:
    task = make_task_dto(
        captain=make_helper(member=make_member(member_id=77)),
        helpers=[make_helper(), make_helper(member=make_member(member_id=51))],
        helper_min_count=2,
    )
    assert _get_task_warnings(task) == []


def test_get_task_warnings_no_captain() -> None:
    task = make_task_dto(
        captain=None,
        helpers=[make_helper(), make_helper(member=make_member(member_id=51))],
        helper_min_count=2,
    )
    assert _get_task_warnings(task) == ["No captain has signed up."]


def test_get_task_warnings_no_helpers() -> None:
    task = make_task_dto(captain=make_helper(), helpers=[], helper_min_count=2)
    assert _get_task_warnings(task) == [
        "No helpers have signed up &mdash; at least 2 are required."
    ]


def test_get_task_warnings_not_enough_helpers_singular() -> None:
    task = make_task_dto(helpers=[make_helper()], helper_min_count=3)
    assert _get_task_warnings(task) == [
        "No captain has signed up.",
        "Only 1 helper has signed up &mdash; at least 3 are required.",
    ]


def test_get_task_warnings_not_enough_helpers_plural() -> None:
    task = make_task_dto(
        helpers=[make_helper(), make_helper(member=make_member(member_id=51))],
        helper_min_count=5,
    )
    assert _get_task_warnings(task) == [
        "No captain has signed up.",
        "Only 2 helpers have signed up &mdash; at least 5 are required.",
    ]


def test_get_task_warnings_required_helpers_singular() -> None:
    task = make_task_dto(helpers=[], helper_min_count=1)
    assert _get_task_warnings(task) == [
        "No captain has signed up.",
        "No helpers have signed up &mdash; at least 1 is required.",
    ]


def test_get_task_warnings_required_helpers_plural() -> None:
    task = make_task_dto(helpers=[], helper_min_count=3)
    assert _get_task_warnings(task) == [
        "No captain has signed up.",
        "No helpers have signed up &mdash; at least 3 are required.",
    ]


def test_get_task_warnings_no_warning_when_min_zero() -> None:
    task = make_task_dto(captain=make_helper(), helpers=[], helper_min_count=0)
    assert _get_task_warnings(task) == []


# ==============================================================================
# _HelperTaskChanges
# ==============================================================================


def test_task_changes_no_diff_produces_empty_summary() -> None:
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), {})
    assert changes.summary == []
    assert changes.relevant_details == {}


def test_task_changes_title() -> None:
    diff: dict[str, DiffEntry] = {"title": {"old": "Old", "new": "New"}}
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert changes.summary == ["title"]
    assert changes.relevant_details == {"Previous title": "Old"}


def test_task_changes_category() -> None:
    diff: dict[str, DiffEntry] = {
        "category.title": {"old": "Maintenance", "new": "Surveillance"},
    }
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert changes.summary == ["category"]
    assert changes.relevant_details == {"Previous category": "Maintenance"}


def test_task_changes_short_description() -> None:
    diff: dict[str, DiffEntry] = {
        "shortDescription": {"old": "Old desc", "new": "New desc"},
    }
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert changes.summary == ["short description"]
    assert changes.relevant_details == {"Previous short description": "Old desc"}


def test_task_changes_long_description_no_details() -> None:
    diff: dict[str, DiffEntry] = {
        "longDescription": {"old": "Old long", "new": "New long"},
    }
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert changes.summary == ["long description"]
    assert changes.relevant_details == {}


def test_task_changes_contact() -> None:
    task = make_task_dto()
    diff: dict[str, DiffEntry] = {
        "contact.firstName": {"old": "Alice", "new": "Bob"},
    }
    changes = _HelperTaskChanges(task, make_task_dto(), diff)
    assert changes.summary == ["contact"]
    assert changes.relevant_details == {
        "Previous contact": format_member_info(task.contact),
    }


def test_task_changes_timing_groups_fields() -> None:
    task = make_task_dto()
    diff: dict[str, DiffEntry] = {
        "startsAt": {"old": "10:00", "new": "11:00"},
        "endsAt": {"old": "18:00", "new": "19:00"},
    }
    changes = _HelperTaskChanges(task, make_task_dto(), diff)
    assert changes.summary == ["timing"]
    assert changes.relevant_details == {
        "Previous timing": format_helper_task_timing(task),
    }


def test_task_changes_helper_min_max_count() -> None:
    task = make_task_dto()
    diff: dict[str, DiffEntry] = {
        "helperMinCount": {"old": 1, "new": 2},
        "helperMaxCount": {"old": 3, "new": 4},
    }
    changes = _HelperTaskChanges(task, make_task_dto(), diff)
    assert changes.summary == ["helpers needed"]
    assert changes.relevant_details == {
        "Previous helpers needed": format_helper_task_min_max_helpers(task),
    }


def test_task_changes_urgent_true() -> None:
    diff: dict[str, DiffEntry] = {"urgent": {"old": False, "new": True}}
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(urgent=True), diff)
    assert changes.summary == ["urgent"]
    assert changes.relevant_details == {}


def test_task_changes_urgent_false() -> None:
    diff: dict[str, DiffEntry] = {"urgent": {"old": True, "new": False}}
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(urgent=False), diff)
    assert changes.summary == ["not urgent"]
    assert changes.relevant_details == {}


def test_task_changes_published() -> None:
    diff: dict[str, DiffEntry] = {"published": {"old": False, "new": True}}
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(published=True), diff)
    assert changes.summary == ["published"]
    assert changes.relevant_details == {}


def test_task_changes_unpublished() -> None:
    diff: dict[str, DiffEntry] = {"published": {"old": True, "new": False}}
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(published=False), diff)
    assert changes.summary == ["unpublished"]
    assert changes.relevant_details == {}


def test_task_changes_captain() -> None:
    diff: dict[str, DiffEntry] = {
        "captain.member.firstName": {"old": "Alice", "new": "Bob"},
    }
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert changes.summary == ["captain"]
    assert changes.relevant_details == {}


def test_task_changes_helpers() -> None:
    diff: dict[str, DiffEntry] = {
        "helpers.0.member.firstName": {"old": "Alice", "new": "Bob"},
    }
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert changes.summary == ["helpers"]
    assert changes.relevant_details == {}


def test_task_changes_status_marked_as_done() -> None:
    diff: dict[str, DiffEntry] = {
        "marked_as_done_at": {"old": None, "new": "2026-01-01"},
    }
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert changes.summary == ["status"]
    assert changes.relevant_details == {}


def test_task_changes_status_validated() -> None:
    diff: dict[str, DiffEntry] = {
        "validated_at": {"old": None, "new": "2026-01-01"},
        "validation_comment": {"old": None, "new": "OK"},
    }
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert changes.summary == ["status"]
    assert changes.relevant_details == {}


def test_task_changes_id_fields_ignored() -> None:
    diff: dict[str, DiffEntry] = {
        "id": {"old": 1, "new": 2},
        "contactId": {"old": 1, "new": 2},
        "category.id": {"old": 1, "new": 2},
    }
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert changes.summary == []
    assert changes.relevant_details == {}


def test_task_changes_captain_licence() -> None:
    diff: dict[str, DiffEntry] = {
        "captainRequiredLicenceInfo.licence": {"old": "D", "new": "B"},
    }
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert changes.summary == ["captain required licence"]
    assert changes.relevant_details == {"Previous captain required licence": "D"}


def test_task_changes_undetected_field_logged_and_included() -> None:
    diff: dict[str, DiffEntry] = {
        "someUnknownField": {"old": "x", "new": "y"},
    }
    changes = _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert changes.summary == ["some unknown field"]
    assert changes.relevant_details == {"Previous some unknown field:": "x"}


def test_task_changes_multiple_combined() -> None:
    task = make_task_dto()
    diff: dict[str, DiffEntry] = {
        "title": {"old": "Old", "new": "New"},
        "urgent": {"old": False, "new": True},
        "startsAt": {"old": "10:00", "new": "11:00"},
    }
    changes = _HelperTaskChanges(task, make_task_dto(urgent=True), diff)
    assert set(changes.summary) == {"title", "urgent", "timing"}
    assert changes.relevant_details == {
        "Previous title": "Old",
        "Previous timing": format_helper_task_timing(task),
    }


def test_task_changes_diff_is_deep_copied() -> None:
    diff: dict[str, DiffEntry] = {
        "title": {"old": "Old", "new": "New"},
        "startsAt": {"old": "10:00", "new": "11:00"},
    }
    original_keys = set(diff.keys())
    _HelperTaskChanges(make_task_dto(), make_task_dto(), diff)
    assert set(diff.keys()) == original_keys
