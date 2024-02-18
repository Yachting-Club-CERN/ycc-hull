"""
Member API endpoints.
"""
from collections.abc import Sequence
from datetime import date

from fastapi import APIRouter, Depends
from ycc_hull.auth import User, auth

from ycc_hull.controllers.members_controller import MembersController
from ycc_hull.api.errors import (
    create_http_exception_403,
)
from ycc_hull.models.dtos import MemberPublicInfoDto, MembershipTypeDto, UserDto

api_members = APIRouter(dependencies=[Depends(auth)])
controller = MembersController()


@api_members.get("/api/v1/members")
async def members_get(
    year: int | None = None, user: User = Depends(auth)
) -> Sequence[MemberPublicInfoDto]:
    _check_can_access_year(year, user)
    current_year = date.today().year

    if year != current_year and not (user.admin or user.committee_member):
        raise create_http_exception_403(
            f"You do not have permission to list members for {year}"
        )

    return await controller.find_all_public_infos(year=year)


@api_members.get("/api/v1/membership-types")
async def membership_types_get() -> Sequence[MembershipTypeDto]:
    return await controller.find_all_membership_types()


@api_members.get("/api/v1/users")
async def users_get(user: User = Depends(auth)) -> Sequence[UserDto]:
    if not user.admin:
        raise create_http_exception_403("You do not have permission to list users")

    return await controller.find_all_users()


def _check_can_access_year(year: int | None, user: User) -> None:
    current_year = date.today().year

    if year != current_year and not (user.admin or user.committee_member):
        raise create_http_exception_403(
            f"You do not have permission to view members for {year}"
        )
