"""
Member API endpoints.
"""
from datetime import date
from typing import Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException
from ycc_hull.auth import AuthInfo, auth

from ycc_hull.controllers.members_controller import MembersController
from ycc_hull.error import raise_401
from ycc_hull.models.dtos import MemberPublicInfoDto, MembershipTypeDto, UserDto

api_members = APIRouter(dependencies=[Depends(auth)])


@api_members.get("/api/v0/members")
async def members_get(
    year: Optional[int] = None, auth_info: AuthInfo = Depends(auth)
) -> Sequence[MemberPublicInfoDto]:
    current_year = date.today().year

    if year != current_year and not (auth_info.admin or auth_info.committee_member):
        raise HTTPException(
            status_code=403,
            detail=f"You do not have permission to list members for {year}",
        )

    return await MembersController.find_all_public_infos(year)


@api_members.get("/api/v0/membership-types")
async def membership_types_get() -> Sequence[MembershipTypeDto]:
    return await MembersController.find_all_membership_types()


@api_members.get("/api/v0/users")
async def users_get(auth_info: AuthInfo = Depends(auth)) -> Sequence[UserDto]:
    if not auth_info.admin:
        raise raise_401()

    return await MembersController.find_all_users()
