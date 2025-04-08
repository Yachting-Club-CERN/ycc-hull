"""
Audit log controller.
"""

from collections.abc import Sequence

from sqlalchemy import delete, desc, select
from sqlalchemy.orm import defer

from ycc_hull.controllers.base_controller import BaseController
from ycc_hull.controllers.exceptions import ControllerNotFoundException
from ycc_hull.db.entities import AuditLogEntryEntity
from ycc_hull.models.audit_log_dtos import (
    AuditLogEntriesDeleteRequestDto,
    AuditLogEntryDto,
)
from ycc_hull.models.user import User


class AuditLogController(BaseController):
    """
    Audit Log controller. Returns DTO objects.
    """

    async def find_all_entries(self) -> Sequence[AuditLogEntryDto]:
        return await self.database_context.query_all(
            select(AuditLogEntryEntity)
            .options(
                defer(AuditLogEntryEntity.data, raiseload=True),
            )
            .order_by(desc(AuditLogEntryEntity.created_at)),
            async_transformer=AuditLogEntryDto.create_without_large_fields,
        )

    async def get_entry_by_id(
        self,
        entry_id: int,
    ) -> AuditLogEntryDto:
        entries = await self.database_context.query_all(
            select(AuditLogEntryEntity).where(AuditLogEntryEntity.id == entry_id),
            async_transformer=AuditLogEntryDto.create,
        )

        if entries:
            return entries[0]

        raise ControllerNotFoundException("Audit log entry not found")

    async def delete_entries(
        self, request: AuditLogEntriesDeleteRequestDto, user: User
    ) -> int:
        with self.database_context.session() as session:
            self._logger.info(
                "Deleting audit log entries older than %s, user: %s",
                request.cutoff_date,
                user.username,
            )

            result = session.execute(
                delete(AuditLogEntryEntity).where(
                    AuditLogEntryEntity.created_at < request.cutoff_date,
                )
            )

            session.commit()

            self._audit_log(
                session, user, f"AuditLog/DeleteEntriesBefore/{request.cutoff_date}"
            )
            return result.rowcount  # Number of rows deleted
