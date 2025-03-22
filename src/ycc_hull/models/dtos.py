"""
General API DTO classes.
"""

from datetime import date

from pydantic import Field

from ycc_hull.db.entities import (BoatEntity, HolidayEntity, LicenceInfoEntity,
                                  MemberEntity, MembershipTypeEntity,
                                  UserEntity)
from ycc_hull.models.base import CamelisedBaseModelWithEntity

_UNKNOWN = "<unknown>"


class BoatDto(CamelisedBaseModelWithEntity[BoatEntity]):
    """
    DTO for a boat.
    """

    id: int
    name: str
    type: str
    licence: str
    class_: str = Field(alias="class")
    capacity: int | None
    # ycc_num / number is irrelevant for the model
    table_position: int | None

    @staticmethod
    async def create(
        boat: BoatEntity,
    ) -> "BoatDto":
        return BoatDto(
            entity=boat,
            id=boat.boat_id,
            name=boat.name,
            type=boat.type,
            licence=boat.license,
            class_=boat.class_,
            capacity=boat.capacity,
            table_position=boat.table_pos,
        )


class HolidayDto(CamelisedBaseModelWithEntity[HolidayEntity]):
    """
    DTO for a holiday.
    """

    date: date
    label: str
    # id is irrelevant for the model

    @staticmethod
    async def create(
        holiday: HolidayEntity,
    ) -> "HolidayDto":
        return HolidayDto(
            entity=holiday,
            date=holiday.day.date(),
            label=holiday.label,
        )


class LicenceInfoDto(CamelisedBaseModelWithEntity[LicenceInfoEntity]):
    """
    DTO for a YCC licence info.
    """

    id: int
    licence: str

    @staticmethod
    async def create(
        licence_info: LicenceInfoEntity,
    ) -> "LicenceInfoDto":
        return LicenceInfoDto(
            entity=licence_info,
            id=licence_info.infoid,
            licence=licence_info.nlicence,
        )


class LicenceDetailedInfoDto(LicenceInfoDto):
    """
    DTO for a YCC licence detailed info.
    """

    description: str
    licence: str

    @staticmethod
    async def create(
        licence_info: LicenceInfoEntity,
    ) -> "LicenceDetailedInfoDto":
        props = (await LicenceInfoDto.create(licence_info)).model_dump()
        props["description"] = licence_info.description
        return LicenceDetailedInfoDto(**props)


class MemberPublicInfoDto(CamelisedBaseModelWithEntity[MemberEntity]):
    """
    DTO for a member, containing information public to all active members.
    """

    id: int
    username: str
    first_name: str
    last_name: str
    email: str | None
    mobile_phone: str | None
    home_phone: str | None
    work_phone: str | None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @staticmethod
    async def create(
        member: MemberEntity,
    ) -> "MemberPublicInfoDto":
        return MemberPublicInfoDto(
            entity=member,
            id=member.id,
            username=member.user.logon_id if member.user else _UNKNOWN,
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
    async def create(
        member: MemberEntity,
    ) -> "MemberSensitiveInfoDto":
        props = (await MemberPublicInfoDto.create(member)).model_dump()
        props["id"] = member.id
        props["membership_type"] = member.membership
        return MemberSensitiveInfoDto(**props)


class MembershipTypeDto(CamelisedBaseModelWithEntity[MembershipTypeEntity]):
    """
    DTO for a membership type.
    """

    id: int
    name: str
    description_en: str
    description_fr: str
    comments: str | None

    @staticmethod
    async def create(
        membership_type: MembershipTypeEntity,
    ) -> "MembershipTypeDto":
        return MembershipTypeDto(
            entity=membership_type,
            id=membership_type.mb_id,
            name=membership_type.mb_name,
            description_en=membership_type.e_desc,
            description_fr=membership_type.f_desc,
            comments=membership_type.comments,
        )


class UserDto(CamelisedBaseModelWithEntity[UserEntity]):
    """
    DTO for a user.
    """

    id: int
    username: str

    @staticmethod
    async def create(
        user: UserEntity,
    ) -> "UserDto":
        return UserDto(
            entity=user,
            id=user.member_id,
            username=user.logon_id,
            # Ignore sensitive info
        )
