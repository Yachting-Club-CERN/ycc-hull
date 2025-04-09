"""
Audit log API endpoints.
"""

from collections.abc import Sequence

from fastapi import APIRouter, Depends, Response, status

from ycc_hull.api.errors import create_http_exception_403
from ycc_hull.app_controllers import get_audit_log_controller
from ycc_hull.auth import User, auth
from ycc_hull.controllers.audit_log_controller import AuditLogController
from ycc_hull.models.audit_log_dtos import (
    AuditLogEntriesDeleteRequestDto,
    AuditLogEntryDto,
)

api_audit_log = APIRouter(dependencies=[Depends(auth)])


@api_audit_log.get("/api/v1/audit-log/entries")
async def audit_log_entries_get(
    user: User = Depends(auth),
    controller: AuditLogController = Depends(get_audit_log_controller),
) -> Sequence[AuditLogEntryDto]:
    _check_can_access(user)

    return await controller.find_all_entries()


@api_audit_log.get("/api/v1/audit-log/entries/{entry_id}")
async def audit_log_entries_get_by_id(
    entry_id: int,
    user: User = Depends(auth),
    controller: AuditLogController = Depends(get_audit_log_controller),
) -> AuditLogEntryDto:
    _check_can_access(user)

    return await controller.get_entry_by_id(entry_id)


@api_audit_log.delete("/api/v1/audit-log/entries")
async def audit_log_entries_delete(
    request: AuditLogEntriesDeleteRequestDto,
    user: User = Depends(auth),
    controller: AuditLogController = Depends(get_audit_log_controller),
) -> Response:
    _check_can_access(user)

    await controller.delete_entries(request, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _check_can_access(user: User) -> None:
    if not user.helpers_app_admin:
        raise create_http_exception_403("Forbidden")
