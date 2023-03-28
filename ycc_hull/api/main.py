"""
Main API endpoints.
"""
from typing import Any, Callable, Sequence, TypeVar

from fastapi import APIRouter
from sqlalchemy import select, Select
from sqlalchemy.orm import Session

from ycc_hull.db.engine import get_db_engine
from ycc_hull.db.models import Boat, Holiday, Member, MembershipType, User

from .dtos import BoatDto, HolidayDto, MemberDto, MembershipTypeDto, UserDto

api_main = APIRouter()


@api_main.get("/api/v0/boats")
async def boats_get() -> Sequence[BoatDto]:
    return _query_all(select(Boat).order_by(Boat.table_pos), BoatDto.create)


@api_main.get("/api/v0/holidays")
async def holidays_get() -> Sequence[HolidayDto]:
    return _query_all(select(Holiday).order_by(Holiday.day), HolidayDto.create)


@api_main.get("/api/v0/members")
async def members_get() -> Sequence[MemberDto]:
    return _query_all(
        select(Member).order_by(Member.name, Member.firstname), MemberDto.create
    )


@api_main.get("/api/v0/membership-types")
async def membership_types_get() -> Sequence[MembershipTypeDto]:
    return _query_all(
        select(MembershipType).order_by(MembershipType.e_desc),
        MembershipTypeDto.create,
    )


@api_main.get("/api/v0/users")
async def users_get() -> Sequence[UserDto]:
    return _query_all(select(User).order_by(User.logon_id), UserDto.create)


T = TypeVar("T")


def _query_all(statement: Select, dto_factory: Callable[[Any], T]) -> Sequence[T]:
    with Session(get_db_engine()) as session:
        return [dto_factory(row) for row in session.scalars(statement)]
