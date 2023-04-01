"""
Member API endpoints.
"""
from datetime import date
from typing import Optional, Sequence

from fastapi import APIRouter, HTTPException

from ycc_hull.controllers.members_controller import MembersController
from ycc_hull.models.dtos import MemberPublicInfoDto, MembershipTypeDto, UserDto

api_members = APIRouter()


@api_members.get("/api/v0/members")
async def members_get(year: Optional[int] = None) -> Sequence[MemberPublicInfoDto]:
    pretend_committee_member = False

    current_year = date.today().year

    if year != current_year and not pretend_committee_member:
        raise HTTPException(
            status_code=403,
            detail=f"You do not have permission to list members for {year}",
        )

    return await MembersController.find_all_public_infos(year)


@api_members.get("/api/v0/membership-types")
async def membership_types_get() -> Sequence[MembershipTypeDto]:
    return await MembersController.find_all_membership_types()


@api_members.get("/api/v0/users")
async def users_get() -> Sequence[UserDto]:
    return await MembersController.find_all_users()
