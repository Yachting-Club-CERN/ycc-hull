"""
Playground.
"""
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


def dump_members_and_fees() -> None:
    with database_context.create_session() as session:
        members: ScalarResult[MemberEntity] = session.scalars(
            select(MemberEntity).order_by(MemberEntity.id)
        ).unique()

        for member in members:
            print("=" * 80)
            print(">")
            print(f"> {_username(member)}")
            print(">")
            print()
            dto = MemberSensitiveInfoDto.create(member)
            print(f"xx = {dto}")

            print(
                member.entrance_fee_record.dict()
                if member.entrance_fee_record
                else "<No entrance fee>"
            )
            print()

            for fee_record in member.fee_records:
                print(fee_record.dict())
            print()
            print()


def dump_members_and_licences() -> None:
    with database_context.create_session() as session:
        print("=" * 80)
        members: ScalarResult[MemberEntity] = session.scalars(
            select(MemberEntity)
            .options(joinedload(MemberEntity.licences))
            .order_by(MemberEntity.id)
        ).unique()

        for member in members:
            active_licences = [
                licence.licence_info.nlicence
                for licence in member.licences
                if licence.status
            ]
            inactive_licences = [
                licence.licence_info.nlicence
                for licence in member.licences
                if not licence.status
            ]
            print(
                f"> {_username(member)}: {active_licences} (inactive: {inactive_licences}))"
            )


def dump_helper_tasks() -> None:
    print(
        f"COUNT(HelperTaskCategoryEntity): {database_context.query_count(HelperTaskCategoryEntity)}"
    )
    print(f"COUNT(HelperTaskEntity): {database_context.query_count(HelperTaskEntity)}")
    print(
        f"COUNT(HelperTaskHelperEntity): {database_context.query_count(HelperTaskHelperEntity)}"
    )

    with database_context.create_session() as session:
        helper_tasks: ScalarResult[HelperTaskEntity] = session.scalars(
            select(HelperTaskEntity)
            .options(joinedload(HelperTaskEntity.category))
            .order_by(
                func.coalesce(  # pylint: disable=not-callable
                    HelperTaskEntity.starts_at, HelperTaskEntity.deadline
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

            if helper_task.captain_required_licence_info:
                print(
                    f">   Required licence: {helper_task.captain_required_licence_info.nlicence}"
                )
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
            for helper in helper_task.helpers:
                print(f"- {_username(helper.member)} / {helper.signed_up_at}")

            print()
            print()


def run() -> None:
    dump_members_and_fees()

    print("=" * 80)
    print("=" * 80)
    print("=" * 80)

    dump_members_and_licences()

    print("=" * 80)
    print("=" * 80)
    print("=" * 80)

    dump_helper_tasks()


if __name__ == "__main__":
    run()
