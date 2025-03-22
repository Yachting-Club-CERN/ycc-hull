"""
Test Data API endpoints.
"""

import json
from datetime import date, datetime

import aiofiles
from sqlalchemy import delete
from sqlalchemy.orm import Session

from test_data.generator_config import (
    BOATS_JSON_FILE,
    ENTRANCE_FEE_RECORDS_JSON_FILE,
    FEE_RECORDS_JSON_FILE,
    HELPER_TASK_CATEGORIES_JSON_FILE,
    HELPER_TASK_HELPERS_JSON_FILE,
    HELPER_TASKS_JSON_FILE,
    HELPERS_APP_PERMISSIONS_JSON_FILE,
    HOLIDAYS_JSON_FILE,
    LICENCE_INFOS_JSON_FILE,
    LICENCES_JSON_FILE,
    MEMBERS_JSON_FILE,
    MEMBERSHIP_EXPORTED_JSON_FILE,
    USERS_JSON_FILE,
)
from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.db.entities import (
    AuditLogEntryEntity,
    BaseEntity,
    BoatEntity,
    EntranceFeeRecordEntity,
    FeeRecordEntity,
    HelpersAppPermissionEntity,
    HelperTaskCategoryEntity,
    HelperTaskEntity,
    HelperTaskHelperEntity,
    HolidayEntity,
    LicenceEntity,
    LicenceInfoEntity,
    MemberEntity,
    MembershipTypeEntity,
    UserEntity,
)
from ycc_hull.utils import full_type_name, short_type_name


class _TestDataImporter:
    """
    Test data importer. Able to import data from exported and generated files.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    async def import_exported(
        self, file_path: str, cls: type, commit_on_each: bool = False
    ) -> list:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            data = json.loads(await file.read())
            return await self._import(
                cls, data["results"][0]["items"], commit_on_each=commit_on_each
            )

    async def import_generated(
        self, file_path: str, cls: type, commit_on_each: bool = False
    ) -> list:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            data = json.loads(await file.read())
            return await self._import(cls, data, commit_on_each=commit_on_each)

    async def _import(self, cls: type, entries: list, commit_on_each: bool) -> list:
        for entry in entries:
            entry = self._prepare(entry)
            self._session.add(cls(**entry))
            if commit_on_each:
                self._session.commit()
        return entries

    def _prepare(self, entry: dict) -> dict:
        for key, value in entry.items():
            if isinstance(value, dict) and "@type" in value:
                if value["@type"] == "date":
                    entry[key] = date.fromisoformat(value["value"])
                elif value["@type"] == "datetime":
                    entry[key] = datetime.fromisoformat(value["value"])
                else:
                    raise TypeError(f"Cannot prepare field {key}: {value}")

        # Not necessary to copy the dict
        return entry


class TestDataController(BaseController):
    """
    Test data controller.
    """

    __test__ = False

    async def populate(self) -> list[str]:
        log: list[str] = []

        with self.database_context.session() as session:
            importer = _TestDataImporter(session=session)

            log.extend(await self._populate_holidays(session, importer))
            log.extend(await self._populate_members(session, importer))
            log.extend(await self._populate_boats(session, importer))
            log.extend(await self._populate_licences(session, importer))

            session.commit()
            log.append("Commit")

            log.extend(await self._populate_helpers(session, importer))

        return log

    async def _populate_holidays(
        self, session: Session, importer: _TestDataImporter
    ) -> list[str]:
        log: list[str] = []

        if await self.database_context.query_count(HolidayEntity, session=session):
            log.append("Skipping holidays")
        else:
            entries = await importer.import_generated(HOLIDAYS_JSON_FILE, HolidayEntity)
            log.append(f"Add {len(entries)} holidays")

        return log

    async def _populate_members(
        self, session: Session, importer: _TestDataImporter
    ) -> list[str]:
        log: list[str] = []

        if await self.database_context.query_count(
            MembershipTypeEntity, session=session
        ):
            log.append("Skipping membership types")
        else:
            entries = await importer.import_exported(
                MEMBERSHIP_EXPORTED_JSON_FILE, MembershipTypeEntity
            )

            log.extend(f"Add membership type {entry['mb_name']}" for entry in entries)

        if await self.database_context.query_count(MemberEntity, session=session):
            log.append("Skipping members and related entities")
        else:
            entries = await importer.import_generated(
                ENTRANCE_FEE_RECORDS_JSON_FILE, EntranceFeeRecordEntity
            )
            log.append(f"Add {len(entries)} entrance fee records")

            entries = await importer.import_generated(
                FEE_RECORDS_JSON_FILE, FeeRecordEntity
            )
            log.append(f"Add {len(entries)} fee records")

            entries = await importer.import_generated(MEMBERS_JSON_FILE, MemberEntity)
            log.append(f"Add {len(entries)} members")

            entries = await importer.import_generated(USERS_JSON_FILE, UserEntity)
            log.append(f"Add {len(entries)} users")

        return log

    async def _populate_boats(
        self, session: Session, importer: _TestDataImporter
    ) -> list[str]:
        log: list[str] = []

        if await self.database_context.query_count(BoatEntity, session=session):
            log.append("Skipping boats")
        else:
            entries = await importer.import_generated(BOATS_JSON_FILE, BoatEntity)
            log.append(f"Add {len(entries)} boats")

        return log

    async def _populate_licences(
        self, session: Session, importer: _TestDataImporter
    ) -> list[str]:
        log: list[str] = []

        if await self.database_context.query_count(LicenceInfoEntity, session=session):
            log.append("Skipping licence infos")
        else:
            entries = await importer.import_generated(
                LICENCE_INFOS_JSON_FILE, LicenceInfoEntity
            )
            log.append(f"Add {len(entries)} licence infos")

        if await self.database_context.query_count(LicenceEntity, session=session):
            log.append("Skipping licences")
        else:
            entries = await importer.import_generated(LICENCES_JSON_FILE, LicenceEntity)
            log.append(f"Add {len(entries)} licences")

        return log

    async def _populate_helpers(
        self, session: Session, importer: _TestDataImporter
    ) -> list[str]:
        log: list[str] = []

        if await self.database_context.query_count(
            HelpersAppPermissionEntity, session=session
        ):
            log.append("Skipping helpers app permissions")
        else:
            entries = await importer.import_generated(
                HELPERS_APP_PERMISSIONS_JSON_FILE, HelpersAppPermissionEntity
            )
            log.append(f"Add {len(entries)} helpers app permissions")

        if await self.database_context.query_count(
            HelperTaskCategoryEntity, session=session
        ):
            log.append("Skipping helper task categories")
        else:
            entries = await importer.import_generated(
                HELPER_TASK_CATEGORIES_JSON_FILE, HelperTaskCategoryEntity
            )
            log.append(f"Add {len(entries)} helper task categories")

        if await self.database_context.query_count(HelperTaskEntity, session=session):
            log.append("Skipping helper tasks")
        else:
            entries = await importer.import_generated(
                HELPER_TASKS_JSON_FILE, HelperTaskEntity
            )
            log.append(f"Add {len(entries)} helper tasks")

        session.commit()
        log.append("Commit")

        if await self.database_context.query_count(
            HelperTaskHelperEntity, session=session
        ):
            log.append("Skipping helper task helpers")
        else:
            entries = await importer.import_generated(
                HELPER_TASK_HELPERS_JSON_FILE,
                HelperTaskHelperEntity,
                commit_on_each=True,
            )
            log.append(f"Add {len(entries)} helper task helpers (COMMIT on each)")

        session.commit()
        log.append("Commit")

        return log

    async def clear(self) -> list[str]:
        log: list[str] = []
        classes = (
            # Helpers
            HelpersAppPermissionEntity,
            HelperTaskHelperEntity,
            HelperTaskEntity,
            HelperTaskCategoryEntity,
            # Licences,
            LicenceEntity,
            # Members
            EntranceFeeRecordEntity,
            FeeRecordEntity,
            UserEntity,
            MemberEntity,
            # Licence infos,
            LicenceInfoEntity,
            # Boats
            BoatEntity,
            # General
            AuditLogEntryEntity,
            MembershipTypeEntity,
            HolidayEntity,
        )

        all_entity_classes = set(BaseEntity.__subclasses__())
        unhandled_class_names = [
            f"{full_type_name(cls)}" for cls in all_entity_classes.difference(classes)
        ]

        if unhandled_class_names:
            raise AssertionError(
                f"Some entity classes are not handled: {unhandled_class_names}"
            )

        with self.database_context.session() as session:
            for cls in classes:
                log.append(f"Deleting {short_type_name(cls)} entities")
                session.execute(delete(cls))

            session.commit()
            log.append("Commit")

        return log

    async def repopulate(self) -> list[str]:
        log: list[str] = []

        log.extend(await self.clear())
        log.extend(await self.populate())

        return log
