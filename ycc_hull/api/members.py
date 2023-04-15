"""
Member API endpoints.
"""
from collections.abc import Sequence
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from ycc_hull.auth import User, auth

from ycc_hull.controllers.members_controller import MembersController
from ycc_hull.api.errors import (
    create_http_exception_403,
)
from ycc_hull.models.dtos import MemberPublicInfoDto, MembershipTypeDto, UserDto

api_members = APIRouter(dependencies=[Depends(auth)])


@api_members.get("/api/v0/members")
async def members_get(
    year: Optional[int] = None, user: User = Depends(auth)
) -> Sequence[MemberPublicInfoDto]:
    current_year = date.today().year

    if year != current_year and not (user.admin or user.committee_member):
        raise create_http_exception_403(
            f"You do not have permission to list members for {year}"
        )

    return await MembersController.find_all_public_infos(year)


@api_members.get("/api/v0/membership-types")
async def membership_types_get() -> Sequence[MembershipTypeDto]:
    return await MembersController.find_all_membership_types()


@api_members.get("/api/v0/users")
async def users_get(user: User = Depends(auth)) -> Sequence[UserDto]:
    if not user.admin:
        raise create_http_exception_403("You do not have permission to list users")

    return await MembersController.find_all_users()
