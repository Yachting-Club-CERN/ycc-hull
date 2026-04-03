from collections.abc import Sequence
from datetime import UTC, datetime

from ycc_hull.models.dtos import LicenceInfoDto, MemberPublicInfoDto
from ycc_hull.models.helpers_dtos import (
    HelperTaskCategoryDto,
    HelperTaskDto,
    HelperTaskHelperDto,
)
from ycc_hull.models.user import User


def make_user(  # noqa: PLR0913
    *,
    member_id: int = 1,
    username: str = "testuser",
    email: str = "test@example.com",
    first_name: str = "Test",
    last_name: str = "User",
    groups: tuple[str, ...] = (),
    roles: tuple[str, ...] = (),
) -> User:
    return User(
        member_id=member_id,
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        groups=groups,
        roles=roles,
    )


def make_member(  # noqa: PLR0913
    *,
    member_id: int = 1,
    username: str | None = None,
    first_name: str = "Alice",
    last_name: str = "Smith",
    email: str = "alice@example.com",
    mobile_phone: str | None = None,
    home_phone: str | None = None,
    work_phone: str | None = None,
) -> MemberPublicInfoDto:
    return MemberPublicInfoDto(
        id=member_id,
        username=username if username is not None else f"user{member_id}",
        first_name=first_name,
        last_name=last_name,
        email=email,
        mobile_phone=mobile_phone,
        home_phone=home_phone,
        work_phone=work_phone,
    )


def make_category(
    *,
    category_id: int = 1,
    title: str = "Surveillance",
    short_description: str = "Cat desc",
    long_description: str | None = None,
) -> HelperTaskCategoryDto:
    return HelperTaskCategoryDto(
        id=category_id,
        title=title,
        short_description=short_description,
        long_description=long_description,
    )


def make_helper(
    *,
    member: MemberPublicInfoDto | None = None,
    signed_up_at: datetime = datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
) -> HelperTaskHelperDto:
    return HelperTaskHelperDto(
        member=member
        or make_member(
            member_id=50,
            first_name="Helper",
            last_name="One",
            email="helper@example.com",
        ),
        signed_up_at=signed_up_at,
    )


def make_task_dto(  # noqa: PLR0913
    *,
    task_id: int = 1,
    category: HelperTaskCategoryDto | None = None,
    title: str = "Test Task",
    short_description: str = "Help needed",
    long_description: str | None = None,
    contact: MemberPublicInfoDto | None = None,
    starts_at: datetime | None = datetime(2026, 5, 10, 10, 0, tzinfo=UTC),
    ends_at: datetime | None = datetime(2026, 5, 10, 18, 0, tzinfo=UTC),
    deadline: datetime | None = None,
    urgent: bool = False,
    captain_required_licence_info: LicenceInfoDto | None = None,
    helper_min_count: int = 2,
    helper_max_count: int = 4,
    published: bool = True,
    captain: HelperTaskHelperDto | None = None,
    helpers: Sequence[HelperTaskHelperDto] = (),
    marked_as_done_at: datetime | None = None,
    marked_as_done_by: MemberPublicInfoDto | None = None,
    marked_as_done_comment: str | None = None,
    validated_at: datetime | None = None,
    validated_by: MemberPublicInfoDto | None = None,
    validation_comment: str | None = None,
) -> HelperTaskDto:
    return HelperTaskDto(
        id=task_id,
        category=category or make_category(),
        title=title,
        short_description=short_description,
        long_description=long_description,
        contact=contact or make_member(),
        starts_at=starts_at,
        ends_at=ends_at,
        deadline=deadline,
        urgent=urgent,
        captain_required_licence_info=captain_required_licence_info,
        helper_min_count=helper_min_count,
        helper_max_count=helper_max_count,
        published=published,
        captain=captain,
        helpers=helpers,
        marked_as_done_at=marked_as_done_at,
        marked_as_done_by=marked_as_done_by,
        marked_as_done_comment=marked_as_done_comment,
        validated_at=validated_at,
        validated_by=validated_by,
        validation_comment=validation_comment,
    )
