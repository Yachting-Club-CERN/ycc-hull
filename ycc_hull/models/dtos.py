"""
API DTO Objects.
"""
from datetime import date
from typing import Optional

from humps import camelize
from pydantic import BaseModel

from ycc_hull.db.entities import (
    BoatEntity,
    HolidayEntity,
    MemberEntity,
    MembershipTypeEntity,
    UserEntity,
)


class CamelisedBaseModel(BaseModel):
    """
    Base class for all DTOs which will camelise snake_case attributes when converting to JSON.
    """

    class Config:
        """
        Base config.
        """

        alias_generator = camelize
        allow_population_by_field_name = True


class BoatDto(CamelisedBaseModel):
    """
    DTO for a boat.
    """

    id: int
    name: str
    type: str
    number: int
    licence: str
    class_: str
    table_position: int

    @staticmethod
    def create(
        boat: BoatEntity,
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
    """
    DTO for a holiday.
    """

    date: date
    label: str

    @staticmethod
    def create(
        holiday: HolidayEntity,
    ) -> "HolidayDto":
        return HolidayDto(
            date=holiday.day.date(),
            label=holiday.label,
        )


class MemberPublicInfoDto(CamelisedBaseModel):
    """
    DTO for a member, containing information public to all active members.
    """

    username: str
    first_name: str
    last_name: str
    email: Optional[str]
    mobile_phone: Optional[str]
    home_phone: Optional[str]
    work_phone: Optional[str]

    @staticmethod
    def create(
        member: MemberEntity,
    ) -> "MemberPublicInfoDto":
        return MemberPublicInfoDto(
            username=member.user.logon_id,
            first_name=member.firstname,
            last_name=member.name,
            email=member.e_mail,
            mobile_phone=member.cell_phone,
            home_phone=member.home_phone,
            work_phone=member.work_phone,
        )


class MemberSensitiveInfoDto(MemberPublicInfoDto):
    """
    DTO for a member, containing both information public to all active members and sensitive information.
    """

    id: int
    membership_type: str

    @staticmethod
    def create(
        member: MemberEntity,
    ) -> "MemberSensitiveInfoDto":
        return MemberSensitiveInfoDto(
            id=member.id,
            username=member.user.logon_id,
            first_name=member.firstname,
            last_name=member.name,
            membership_type=member.membership,
            email=member.e_mail,
            mobile_phone=member.cell_phone,
            home_phone=member.home_phone,
            work_phone=member.work_phone,
        )


class MembershipTypeDto(CamelisedBaseModel):
    """
    DTO for a membership type.
    """

    id: int
    name: str
    description_en: str
    description_fr: str
    comments: Optional[str]

    @staticmethod
    def create(
        membership_type: MembershipTypeEntity,
    ) -> "MembershipTypeDto":
        return MembershipTypeDto(
            id=membership_type.mb_id,
            name=membership_type.mb_name,
            description_en=membership_type.e_desc,
            description_fr=membership_type.f_desc,
            comments=membership_type.comments,
        )


class UserDto(CamelisedBaseModel):
    """
    DTO for a user.
    """

    id: int
    username: str

    @staticmethod
    def create(
        user: UserEntity,
    ) -> "UserDto":
        return UserDto(
            id=user.member_id,
            username=user.logon_id
            # Ignore sensitive info
        )
