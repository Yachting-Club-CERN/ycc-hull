"""
Members controller.
"""
from typing import Optional, Sequence

from sqlalchemy import and_, or_, select, func

from sqlalchemy.orm import Session
from ycc_hull.db.engine import get_db_engine, query_all
from ycc_hull.db.entities import (
    FeeRecordEntity,
    LicenceEntity,
    MemberEntity,
    MembershipTypeEntity,
    UserEntity,
)
from ycc_hull.models.dtos import (
    MemberPublicInfoDto,
    MembershipTypeDto,
    UserDto,
)


class MembersController:
    """
    Members controller. Returns DTO objects.
    """

    @staticmethod
    async def find_all_public_infos(
        year: Optional[int] = None,
    ) -> Sequence[MemberPublicInfoDto]:
        query = select(MemberEntity)

        if year:
            query = (
                query.outerjoin(FeeRecordEntity)
                .filter(
                    or_(
                        and_(
                            MemberEntity.membership.like("H"),
                            MemberEntity.member_entrance <= year,
                        ),
                        FeeRecordEntity.year_f == year,
                    )
                )
                .distinct()
            )

        return query_all(
            query.order_by(MemberEntity.name, MemberEntity.firstname),
            MemberPublicInfoDto.create,
        )

    @staticmethod
    async def find_all_membership_types() -> Sequence[MembershipTypeDto]:
        return query_all(
            select(MembershipTypeEntity).order_by(MembershipTypeEntity.e_desc),
            MembershipTypeDto.create,
        )

    @staticmethod
    async def find_all_users() -> Sequence[UserDto]:
        return query_all(
            select(UserEntity).order_by(UserEntity.logon_id), UserDto.create
        )
