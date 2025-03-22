"""
Members controller.
"""

from collections.abc import Sequence

from sqlalchemy import and_, or_, select

from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.db.entities import (
    FeeRecordEntity,
    MemberEntity,
    MembershipTypeEntity,
    UserEntity,
)
from ycc_hull.models.dtos import MemberPublicInfoDto, MembershipTypeDto, UserDto


class MembersController(BaseController):
    """
    Members controller. Returns DTO objects.
    """

    async def find_all_public_infos(
        self,
        *,
        year: int,
    ) -> Sequence[MemberPublicInfoDto]:
        query = (
            select(MemberEntity)
            .outerjoin(FeeRecordEntity)
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

        return await self.database_context.query_all(
            query.order_by(MemberEntity.name, MemberEntity.firstname),
            async_transformer=MemberPublicInfoDto.create,
        )

    async def find_all_membership_types(self) -> Sequence[MembershipTypeDto]:
        return await self.database_context.query_all(
            select(MembershipTypeEntity).order_by(MembershipTypeEntity.e_desc),
            async_transformer=MembershipTypeDto.create,
        )

    async def find_all_users(self) -> Sequence[UserDto]:
        return await self.database_context.query_all(
            select(UserEntity).order_by(UserEntity.logon_id),
            async_transformer=UserDto.create,
        )
