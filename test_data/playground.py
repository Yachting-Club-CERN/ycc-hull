"""
Playground.
"""
from sqlalchemy import ScalarResult, func, select
from sqlalchemy.orm import Session, joinedload

from ycc_hull.db.engine import _create_db_engine
from ycc_hull.db.entities import (
    HelperTaskEntity,
    MemberEntity,
)
from ycc_hull.models.dtos import MemberSensitiveInfoDto

engine = _create_db_engine(db_engine_echo=True)


def dump_members_and_fees() -> None:
    with Session(engine) as session:
        members: ScalarResult[MemberEntity] = session.scalars(
            select(MemberEntity).order_by(MemberEntity.id)
        ).unique()

        for member in members:
            print("=" * 80)
            print(">")
            print(f"> {member.user.logon_id}")
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
    with Session(engine) as session:
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
                f"> {member.user.logon_id}: {active_licences} (inactive: {inactive_licences}))"
            )


def dump_helper_tasks() -> None:
    with Session(engine) as session:
        helper_tasks: ScalarResult[HelperTaskEntity] = session.scalars(
            select(HelperTaskEntity)
            .options(joinedload(HelperTaskEntity.category))
            .order_by(
                func.coalesce(  # pylint: disable=not-callable
                    HelperTaskEntity.start, HelperTaskEntity.deadline
                )
            )
        ).unique()

        for helper_task in helper_tasks:
            print("=" * 80)
            print(">")
            print(f"> {helper_task.category.title} / {helper_task.title}")
            print(
                f">   Timing: {helper_task.start} / {helper_task.end} / {helper_task.deadline}"
            )

            print(f">   Required licence: {helper_task.captain_required_licence}")
            print(
                f">   Helpers needed: {helper_task.helpers_min_count} - {helper_task.helpers_max_count}"
            )
            print(">")
            print()

            print(
                f"Captain: {helper_task.captain} / {helper_task.captain_subscribed_at}"
            )
            print()

            print("Helpers:")
            for helper in helper_task.helpers:
                print(f"- {helper.member.user.logon_id} / {helper.subscribed_at}")

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
