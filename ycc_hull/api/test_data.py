"""
Test Data API endpoints.
"""
import json
from typing import Any, List

from fastapi import APIRouter
from sqlalchemy import delete
from sqlalchemy.orm import Session
from ycc_hull.api.main import (
    boats_get,
    holidays_get,
    members_get,
    membership_types_get,
    users_get,
)
from ycc_hull.db.engine import get_db_engine
from ycc_hull.db.models import Boat, Holiday, Member, MembershipType, User

api_test_data = APIRouter()


class TestDataImporter:
    def __init__(self, directory: str, session: Session):
        self._directory = directory
        self._session = session

    def import_exported(self, file_path: str, cls: Any) -> List:
        with open(
            f"{self._directory}/exported/{file_path}", "r", encoding="utf-8"
        ) as file:
            content = json.load(file)
            entries = content["results"][0]["items"]
            for entry in entries:
                self._session.add(cls(**entry))
            return entries

    def import_generated(self, file_path: str, cls: Any) -> List:
        with open(
            f"{self._directory}/generated/{file_path}", "r", encoding="utf-8"
        ) as file:
            entries = json.load(file)
            for entry in entries:
                self._session.add(cls(**entry))
            return entries


@api_test_data.post("/api/v0/test-data/populate")
async def populate() -> List[str]:
    log: List[str] = []

    with Session(get_db_engine()) as session:
        session: Session
        importer = TestDataImporter(directory="test_data/", session=session)

        if await holidays_get():
            log.append("Skipping holidays")
        else:
            entries = importer.import_exported(
                "HOLIDAYS_DATA_TABLE.json-formatted", Holiday
            )
            log.append(f"Add {len(entries)} holidays")

        if await membership_types_get():
            log.append("Skipping membership types")
        else:
            entries = importer.import_exported(
                "MEMBERSHIP_DATA_TABLE.json-formatted", MembershipType
            )

            log.extend(f"Add membership type {entry['mb_name']}" for entry in entries)

        if await members_get():
            log.append("Skipping members")
        else:
            entries = importer.import_generated("Members.json", Member)
            log.append(f"Add {len(entries)} members")

        if await users_get():
            log.append("Skipping users")
        else:
            entries = importer.import_generated("Users.json", User)
            log.append(f"Add {len(entries)} users")

        if await boats_get():
            log.append("Skipping boats")
        else:
            entries = importer.import_generated("Boats.json", Boat)
            log.append(f"Add {len(entries)} boats")

        session.commit()
        log.append("Commit")

    return log


@api_test_data.post("/api/v0/test-data/clear")
async def clear() -> List[str]:
    log: List[str] = []

    with Session(get_db_engine()) as session:
        log.append("Deleting boats")
        session.execute(delete(Boat))

        log.append("Deleting membership types")
        session.execute(delete(MembershipType))

        log.append("Deleting users")
        session.execute(delete(User))

        log.append("Deleting members")
        session.execute(delete(Member))

        log.append("Deleting holidays")
        session.execute(delete(Holiday))

        session.commit()
        log.append("Commit")

    return log


@api_test_data.post("/api/v0/test-data/repopulate")
async def repopulate() -> List[str]:
    log: List[str] = []

    log.extend(await clear())
    log.extend(await populate())

    return log
