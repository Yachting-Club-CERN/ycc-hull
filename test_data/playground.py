"""
Playground.
"""

import asyncio

from sqlalchemy import ScalarResult, func, select
from sqlalchemy.orm import joinedload
from ycc_hull.config import CONFIG
from ycc_hull.db.context import DatabaseContext

from ycc_hull.db.entities import (
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
    MemberEntity,
)
from ycc_hull.models.dtos import MemberSensitiveInfoDto

database_context = DatabaseContext(database_url=CONFIG.database_url, echo=True)


def _username(member: MemberEntity) -> str:
    return member.user.logon_id if member.user else f"<No user for ID {member.id}>"


async def dump_members_and_fees() -> None:
    with database_context.session() as session:
        members: ScalarResult[MemberEntity] = (
            session.scalars(select(MemberEntity).order_by(MemberEntity.id))
        ).unique()

        for member in members:
            print("=" * 80)
            print(">")
            print(f"> {_username(member)}")
            print(">")
            print()
            dto = await MemberSensitiveInfoDto.create(member)
            print(f"xx = {dto}")

            entrance_fee_record = await member.awaitable_attrs.entrance_fee_record
            print(
                entrance_fee_record.dict()
                if entrance_fee_record
                else "<No entrance fee>"
            )
            print()

            for fee_record in await member.awaitable_attrs.fee_records:
                print(fee_record.dict())
            print()
            print()


async def dump_members_and_licences() -> None:
    with database_context.session() as session:
        print("=" * 80)
        members: ScalarResult[MemberEntity] = (
            session.scalars(
                select(MemberEntity)
                .options(joinedload(MemberEntity.licences))
                .order_by(MemberEntity.id)
            )
        ).unique()

        for member in members:
            licences = await member.awaitable_attrs.licences
            active_licences = [
                licence.licence_info.nlicence for licence in licences if licence.status
            ]
            inactive_licences = [
                licence.licence_info.nlicence
                for licence in licences
                if not licence.status
            ]
            print(
                f"> {_username(member)}: {active_licences} (inactive: {inactive_licences}))"
            )


async def dump_helper_tasks() -> None:
    print(
        f"COUNT(HelperTaskCategoryEntity): {await database_context.query_count(HelperTaskCategoryEntity)}"
    )
    print(
        f"COUNT(HelperTaskEntity): {await database_context.query_count(HelperTaskEntity)}"
    )
    print(
        f"COUNT(HelperTaskHelperEntity): {await database_context.query_count(HelperTaskHelperEntity)}"
    )

    with database_context.session() as session:
        helper_tasks: ScalarResult[HelperTaskEntity] = (
            session.scalars(
                select(HelperTaskEntity)
                .options(joinedload(HelperTaskEntity.category))
                .order_by(
                    func.coalesce(  # pylint: disable=not-callable
                        HelperTaskEntity.starts_at, HelperTaskEntity.deadline
                    )
                )
            )
        ).unique()

        for helper_task in helper_tasks:
            print("=" * 80)
            print(">")
            print(f"> {helper_task.category.title} / {helper_task.title}")
            print(
                f">   Timing: {helper_task.starts_at} / {helper_task.ends_at} / {helper_task.deadline}"
            )

            captain_required_licence_info = (
                await helper_task.awaitable_attrs.captain_required_licence_info
            )
            if captain_required_licence_info:
                print(f">   Required licence: {captain_required_licence_info.nlicence}")
            print(
                f">   Helpers needed: {helper_task.helper_min_count} - {helper_task.helper_max_count}"
            )
            print(">")
            print()

            print(
                f"Captain: {helper_task.captain} / {helper_task.captain_signed_up_at}"
            )
            print()

            print("Helpers:")
            for helper in await helper_task.awaitable_attrs.helpers:
                print(f"- {_username(helper.member)} / {helper.signed_up_at}")

            print()
            print()


async def run() -> None:
    await dump_members_and_fees()

    print("=" * 80)
    print("=" * 80)
    print("=" * 80)

    await dump_members_and_licences()

    print("=" * 80)
    print("=" * 80)
    print("=" * 80)

    await dump_helper_tasks()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
