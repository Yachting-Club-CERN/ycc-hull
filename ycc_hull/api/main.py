"""
Main API endpoints.
"""
from typing import List

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from ycc_hull.db.engine import get_db_engine
from ycc_hull.db.models import Base, Boat, Holiday, Member, MembershipType, User

api_main = APIRouter()


@api_main.get("/api/v0/boats")
async def boats_get():
    return query_all(Boat)


@api_main.get("/api/v0/holidays")
async def holidays_get():
    return query_all(Holiday)


@api_main.get("/api/v0/members")
async def members_get():
    return query_all(Member)


@api_main.get("/api/v0/membership-types")
async def membership_types_get():
    return query_all(MembershipType)


@api_main.get("/api/v0/users")
async def users_get():
    return query_all(User)


def query_all(cls) -> List[dict]:
    if not cls or not issubclass(cls, Base):
        raise ValueError(f"Invalid class: {cls}")

    with Session(get_db_engine()) as session:
        stmt = select(cls)
        return [row.json_dict() for row in session.scalars(stmt)]
