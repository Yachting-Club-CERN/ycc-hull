"""
Test data generator component for helpers.
"""
from datetime import datetime

from test_data.generator_config import CURRENT_YEAR
from ycc_hull.db.entities import (
    HelpersAppPermissionEntity,
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
)


def generate_helpers_app_permissions() -> list[HelpersAppPermissionEntity]:
    return [
        HelpersAppPermissionEntity(member_id=1, permission="ADMIN"),
        HelpersAppPermissionEntity(member_id=2, permission="EDITOR"),
        HelpersAppPermissionEntity(member_id=3, permission="EDITOR"),
    ]


def generate_helper_task_categories() -> list[HelperTaskCategoryEntity]:
    return [
        HelperTaskCategoryEntity(
            id=1, title="Surveillance", short_description="Q-boat surveillance"
        ),
        HelperTaskCategoryEntity(
            id=2, title="Maintenance / General", short_description="General maintenance"
        ),
    ]


def generate_helper_tasks() -> list[HelperTaskEntity]:
    # Past: to test that one cannot subscribe
    # Present: to test subscribe
    return [
        # Shift in the past, without captain and helpers
        HelperTaskEntity(
            id=2011,
            category_id=2,
            title="Winter Maintenance J80",
            short_description="Go to BA5 and do something",
            contact_id=1,
            start=datetime(CURRENT_YEAR, 1, 4, 15, 0),
            end=datetime(CURRENT_YEAR, 1, 4, 18, 0),
            deadline=None,
            helpers_min_count=1,
            helpers_max_count=2,
            urgent=False,
            published=True,
        ),
        # Deadline task in the past, with captain and helpers
        HelperTaskEntity(
            id=2012,
            category_id=2,
            title="Winter Maintenance J70",
            short_description="Go to BA5 and do something",
            contact_id=1,
            start=None,
            end=None,
            deadline=datetime(CURRENT_YEAR, 1, 5, 20, 0),
            urgent=False,
            helpers_min_count=2,
            helpers_max_count=2,
            published=True,
            captain_id=1,
            captain_subscribed_at=datetime(CURRENT_YEAR, 1, 4, 18, 23, 46),
        ),
        # Shift in the future
        HelperTaskEntity(
            id=2021,
            category_id=1,
            title="Surveillance",
            short_description="Fictional December D/Y practice",
            contact_id=1,
            start=datetime(CURRENT_YEAR, 12, 1, 18, 0),
            end=datetime(CURRENT_YEAR, 12, 1, 20, 30),
            deadline=None,
            helpers_min_count=1,
            helpers_max_count=2,
            urgent=False,
            published=True,
            captain_required_licence_info_id=9,
        ),
        # Shift in the future
        HelperTaskEntity(
            id=2022,
            category_id=1,
            title="Surveillance",
            short_description="Fictional December D/Y practice",
            contact_id=1,
            start=datetime(CURRENT_YEAR, 12, 2, 18, 0),
            end=datetime(CURRENT_YEAR, 12, 2, 20, 30),
            deadline=None,
            helpers_min_count=1,
            helpers_max_count=2,
            urgent=False,
            published=True,
            captain_required_licence_info_id=9,
        ),
        # Shift in the future, not published
        HelperTaskEntity(
            id=2023,
            category_id=1,
            title="Surveillance",
            short_description="This one is not published",
            contact_id=1,
            start=datetime(CURRENT_YEAR, 12, 3, 18, 0),
            end=datetime(CURRENT_YEAR, 12, 3, 20, 30),
            deadline=None,
            helpers_min_count=1,
            helpers_max_count=2,
            urgent=False,
            published=False,
            captain_required_licence_info_id=9,
        ),
        # Deadline task in the future, 2-3 helpers
        HelperTaskEntity(
            id=2031,
            category_id=2,
            title="Maintenance J70",
            short_description="Hull cleaning",
            contact_id=3,
            start=None,
            end=None,
            deadline=datetime(CURRENT_YEAR, 12, 4, 20),
            helpers_min_count=2,
            helpers_max_count=3,
            urgent=False,
            published=True,
        ),
        # Deadline task in the future, 1 helper, urgent
        HelperTaskEntity(
            id=2032,
            category_id=2,
            title="Maintenance J80",
            short_description="Replace jib sheets",
            contact_id=3,
            start=None,
            end=None,
            deadline=datetime(CURRENT_YEAR, 12, 4, 20, 0),
            helpers_min_count=1,
            helpers_max_count=1,
            urgent=True,
            published=True,
        ),
        # Deadline task in the future, only captain, urgent
        HelperTaskEntity(
            id=2033,
            category_id=2,
            title="Easy Maintenance J80",
            short_description="Buy a new winch and put in the boat",
            contact_id=3,
            start=None,
            end=None,
            deadline=datetime(CURRENT_YEAR, 12, 4, 20, 0),
            helpers_min_count=0,
            helpers_max_count=0,
            urgent=True,
            published=True,
        ),
    ]


def generate_helper_task_helpers() -> list[HelperTaskHelperEntity]:
    return [
        HelperTaskHelperEntity(
            task_id=2012,
            member_id=2,
            subscribed_at=datetime(CURRENT_YEAR, 1, 4, 15, 34, 52),
        ),
        HelperTaskHelperEntity(
            task_id=2012,
            member_id=3,
            subscribed_at=datetime(CURRENT_YEAR, 1, 4, 19, 24, 26),
        ),
    ]
