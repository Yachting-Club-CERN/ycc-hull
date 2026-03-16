"""Member API endpoints."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends

from ycc_hull.api.errors import create_http_error_403
from ycc_hull.app_controllers import get_members_controller
from ycc_hull.auth import User, auth
from ycc_hull.controllers.members_controller import MembersController
from ycc_hull.models.dtos import MemberPublicInfoDto, MembershipTypeDto, UserDto
from ycc_hull.utils import get_now

api_members = APIRouter(dependencies=[Depends(auth)])


@api_members.get("/api/v1/members")
async def members_get(
    year: int,
    user: Annotated[User, Depends(auth)],
    controller: Annotated[MembersController, Depends(get_members_controller)],
) -> Sequence[MemberPublicInfoDto]:
    """List members for a given year."""
    _check_can_access_year(year, user)
    return await controller.find_all_public_infos(year=year)


@api_members.get("/api/v1/membership-types")
async def membership_types_get(
    controller: Annotated[MembersController, Depends(get_members_controller)],
) -> Sequence[MembershipTypeDto]:
    """List all membership types."""
    return await controller.find_all_membership_types()


@api_members.get("/api/v1/users")
async def users_get(
    user: Annotated[User, Depends(auth)],
    controller: Annotated[MembersController, Depends(get_members_controller)],
) -> Sequence[UserDto]:
    """List all users."""
    if not user.admin:
        msg = "You do not have permission to list users"
        raise create_http_error_403(msg)

    return await controller.find_all_users()


def _check_can_access_year(year: int | None, user: User) -> None:
    current_year = get_now().year

    if year != current_year and not (user.admin or user.committee_member):
        msg = f"You do not have permission to view members for {year}"
        raise create_http_error_403(msg)
