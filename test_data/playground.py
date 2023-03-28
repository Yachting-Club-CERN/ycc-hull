"""
Playground.
"""
from sqlalchemy import ScalarResult, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from legacy_password_hashing.password_hashing import hash_ycc_password
from ycc_hull.db.models import (
    Base,
    Boat,
    EntranceFeeRecord,
    FeeRecord,
    Member,
    User,
)

from ycc_hull.db.engine import _create_db_engine

engine = _create_db_engine(db_engine_echo=True)


def dump_members():
    with Session(engine) as session:
        members: ScalarResult[Member] = session.scalars(
            select(Member).order_by(Member.id)
        )
        for member in members:
            print("=" * 80)
            print(">")
            print(f"> {member.user.logon_id}")
            print(">")
            print()

            print(
                member.entrance_fee_record.json_dict()
                if member.entrance_fee_record
                else "<No entrance fee>"
            )
            print()

            for fee_record in member.fee_records:
                print(fee_record.json_dict())
            print()
            print()

    pass


def run():
    dump_members()


if __name__ == "__main__":
    run()
