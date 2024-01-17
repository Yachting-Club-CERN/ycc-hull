"""
Audit log. Persisted in the DB.
"""
import json
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from ycc_hull.auth import User
from ycc_hull.config import CONFIG, Environment
from ycc_hull.db.entities import AuditLogEntryEntity
from ycc_hull.utils import full_type_name

_APPLICATION = (
    "YCC Hull"
    if CONFIG.environment == Environment.PRODUCTION
    else f"YCC Hull {CONFIG.environment}"
)


def _to_json_dict(obj: Any) -> dict:
    if isinstance(obj, datetime):
        return {"@type": "datetime", "value": obj.isoformat()}
    if isinstance(obj, date):
        return {"@type": "date", "value": obj.isoformat()}
    if isinstance(obj, BaseModel):
        return {"@type": full_type_name(obj.__class__), **obj.model_dump(by_alias=True)}
    # Note: entities are not allowed since it is much better to audit the DTOs

    raise TypeError(f"Cannot serialize type: {type(obj)}")


def _to_pretty_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=_to_json_dict)


def create_audit_entry(
    user: User, description: str, data: dict | None = None
) -> AuditLogEntryEntity:
    return AuditLogEntryEntity(
        application=_APPLICATION,
        principal=user.username,
        description=description,
        data=_to_pretty_json(data) if data else None,
    )
