"""
Playground.
"""
from sqlalchemy import ScalarResult, select
from sqlalchemy.orm import Session

from ycc_hull.db.engine import _create_db_engine
from ycc_hull.db.entities import MemberEntity

engine = _create_db_engine(db_engine_echo=True)


def dump_members_and_fees() -> None:
    with Session(engine) as session:
        members: ScalarResult[MemberEntity] = session.scalars(
            select(MemberEntity).order_by(MemberEntity.id)
        )
        for member in members:
            print("=" * 80)
            print(">")
            print(f"> {member.user.logon_id}")
            print(">")
            print()

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
            select(MemberEntity).order_by(MemberEntity.id)
        )
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


def run() -> None:
    dump_members_and_fees()
    dump_members_and_licences()


if __name__ == "__main__":
    run()
