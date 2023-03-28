"""
API DTO Objects.
"""
from datetime import date
from typing import Optional

from humps import camelize
from pydantic import BaseModel

from ycc_hull.db.models import Boat, Holiday, Member, MembershipType, User


class CamelisedBaseModel(BaseModel):
    """
    Base class for all DTOs which will camelise snake_case attributes when converting to JSON.
    """

    class Config:
        alias_generator = camelize
        allow_population_by_field_name = True


class BoatDto(CamelisedBaseModel):
    id: int
    name: str
    type: str
    number: int
    licence: str
    class_: str
    table_position: int

    @staticmethod
    def create(
        boat: Boat,
    ) -> "BoatDto":
        return BoatDto(
            id=boat.boat_id,
            name=boat.name,
            type=boat.type,
            number=boat.ycc_num,
            licence=boat.license,
            class_=boat.class_,
            table_position=boat.table_pos,
        )


class HolidayDto(CamelisedBaseModel):
    date: date
    label: str

    @staticmethod
    def create(
        holiday: Holiday,
    ) -> "HolidayDto":
        return HolidayDto(
            date=holiday.day.date(),
            label=holiday.label,
        )


class MemberDto(CamelisedBaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    membership_type: str

    @staticmethod
    def create(
        member: Member,
    ) -> "MemberDto":
        return MemberDto(
            id=member.id,
            username=member.user.logon_id,
            first_name=member.firstname,
            last_name=member.name,
            membership_type=member.membership,
        )


class MembershipTypeDto(CamelisedBaseModel):
    id: int
    name: str
    description_en: str
    description_fr: str
    comments: Optional[str]

    @staticmethod
    def create(
        membership_type: MembershipType,
    ) -> "MembershipTypeDto":
        return MembershipTypeDto(
            id=membership_type.mb_id,
            name=membership_type.mb_name,
            description_en=membership_type.e_desc,
            description_fr=membership_type.f_desc,
            comments=membership_type.comments,
        )


class UserDto(CamelisedBaseModel):
    id: int
    username: str

    @staticmethod
    def create(
        user: User,
    ) -> "UserDto":
        return UserDto(
            id=user.member_id,
            username=user.logon_id
            # Ignore sensitive info
        )
