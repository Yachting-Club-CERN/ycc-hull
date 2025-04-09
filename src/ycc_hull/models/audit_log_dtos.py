"""
Audit log API DTO classes.
"""

from datetime import date, datetime

from ycc_hull.db.entities import AuditLogEntryEntity
from ycc_hull.models.base import CamelisedBaseModel, CamelisedBaseModelWithEntity


class AuditLogEntryDto(CamelisedBaseModelWithEntity[AuditLogEntryEntity]):
    """
    DTO for an audit log entry.
    """

    id: int
    created_at: datetime
    application: str
    principal: str
    description: str
    data: str | None

    @classmethod
    async def create(cls, entry: AuditLogEntryEntity) -> "AuditLogEntryDto":
        return await cls._create(
            entry,
            data=await entry.awaitable_attrs.data,
        )

    @classmethod
    async def create_without_large_fields(
        cls, entry: AuditLogEntryEntity
    ) -> "AuditLogEntryDto":
        return await cls._create(
            entry,
            data=None,
        )

    @staticmethod
    async def _create(
        entry: AuditLogEntryEntity,
        *,
        data: str | None,
    ) -> "AuditLogEntryDto":
        return AuditLogEntryDto(
            entity=entry,
            id=entry.id,
            created_at=entry.created_at,
            application=entry.application,
            principal=entry.principal,
            description=entry.description,
            data=data,
        )


class AuditLogEntriesDeleteRequestDto(CamelisedBaseModel):
    """
    DTO for an audit log delete request.
    """

    cutoff_date: date
