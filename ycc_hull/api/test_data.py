"""
Test Data API endpoints.
"""
import json
from datetime import date, datetime
from typing import List

import aiofiles
from fastapi import APIRouter
from sqlalchemy import delete
from sqlalchemy.orm import Session

from ycc_hull.api.main import boats_get, holidays_get, members_get, membership_types_get
from ycc_hull.db.engine import get_db_engine
from ycc_hull.db.models import (
    Base,
    Boat,
    EntranceFeeRecord,
    FeeRecord,
    Holiday,
    Member,
    MembershipType,
    User,
)

api_test_data = APIRouter()


class TestDataImporter:
    """
    Test data importer. Able to import data from exported and generated files.
    """

    def __init__(self, directory: str, session: Session):
        self._directory = directory
        self._session = session

    async def import_exported(self, file_path: str, cls: type) -> List:
        async with aiofiles.open(
            f"{self._directory}/exported/{file_path}", "r", encoding="utf-8"
        ) as file:
            data = json.loads(await file.read())
            return self._import(cls, data["results"][0]["items"])

    async def import_generated(self, file_path: str, cls: type) -> list:
        async with aiofiles.open(
            f"{self._directory}/generated/{file_path}", "r", encoding="utf-8"
        ) as file:
            data = json.loads(await file.read())
            return self._import(cls, data)

    def _import(self, cls: type, entries: list) -> list:
        for entry in entries:
            entry = self._prepare(entry)
            self._session.add(cls(**entry))
        return entries

    def _prepare(self, entry: dict) -> dict:
        for key, value in entry.items():
            if isinstance(value, dict) and "@type" in value:
                if value["@type"] == "date":
                    entry[key] = date.fromisoformat(value["@value"])
                elif value["@type"] == "datetime":
                    entry[key] = datetime.fromisoformat(value["@value"])
                else:
                    raise TypeError(f"Cannot prepare field {key}: {value}")

        # Not necessary to copy the dict
        return entry


@api_test_data.post("/api/v0/test-data/populate")
async def populate() -> List[str]:
    log: List[str] = []

    with Session(get_db_engine()) as session:
        importer = TestDataImporter(directory="test_data/", session=session)

        if await holidays_get():
            log.append("Skipping holidays")
        else:
            entries = await importer.import_exported(
                "HOLIDAYS_DATA_TABLE.json-formatted", Holiday
            )
            log.append(f"Add {len(entries)} holidays")

        if await membership_types_get():
            log.append("Skipping membership types")
        else:
            entries = await importer.import_exported(
                "MEMBERSHIP_DATA_TABLE.json-formatted", MembershipType
            )

            log.extend(f"Add membership type {entry['mb_name']}" for entry in entries)

        if await members_get():
            log.append("Skipping members and related entities")
        else:
            entries = await importer.import_generated(
                "EntranceFeeRecords.json", EntranceFeeRecord
            )
            log.append(f"Add {len(entries)} entrance fee records")

            entries = await importer.import_generated("FeeRecords.json", FeeRecord)
            log.append(f"Add {len(entries)} fee records")

            entries = await importer.import_generated("Members.json", Member)
            log.append(f"Add {len(entries)} members")

            entries = await importer.import_generated("Users.json", User)
            log.append(f"Add {len(entries)} users")

        if await boats_get():
            log.append("Skipping boats")
        else:
            entries = await importer.import_generated("Boats.json", Boat)
            log.append(f"Add {len(entries)} boats")

        session.commit()
        log.append("Commit")

    return log


@api_test_data.post("/api/v0/test-data/clear")
async def clear() -> List[str]:
    log: List[str] = []
    classes = (
        # Boats
        Boat,
        # Members
        EntranceFeeRecord,
        FeeRecord,
        User,
        Member,
        # General
        MembershipType,
        Holiday,
    )

    all_model_classes = set(Base.__subclasses__())
    unhandled_class_names = [
        f"{cls.__qualname__}" for cls in all_model_classes.difference(classes)
    ]

    if unhandled_class_names:
        raise Exception(f"Some model classes are not handled: {unhandled_class_names}")

    with Session(get_db_engine()) as session:
        for cls in classes:
            log.append(f"Deleting {cls.__qualname__} entities")
            session.execute(delete(cls))

        session.commit()
        log.append("Commit")

    return log


@api_test_data.post("/api/v0/test-data/repopulate")
async def repopulate() -> List[str]:
    log: List[str] = []

    log.extend(await clear())
    log.extend(await populate())

    return log
