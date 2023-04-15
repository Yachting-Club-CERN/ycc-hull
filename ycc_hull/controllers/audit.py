"""
Audit log. Persisted in the DB.
"""
import json
from typing import Any, Optional

from pydantic import BaseModel
from ycc_hull.auth import User
from ycc_hull.config import CONFIG, Environment
from ycc_hull.db.entities import AuditLogEntryEntity, BaseEntity
from datetime import datetime, date

_APPLICATION = (
    "YCC Hull"
    if CONFIG.environment == Environment.PRODUCTION
    else f"YCC Hull {CONFIG.environment}"
)


def _to_json_dict(obj: Any) -> dict:
    if isinstance(obj, datetime):
        return {"@type": "datetime", "@value": obj.isoformat()}
    if isinstance(obj, date):
        return {"@type": "date", "@value": obj.isoformat()}
    if isinstance(obj, BaseEntity) or isinstance(obj, BaseModel):
        return obj.dict()

    raise TypeError(f"Cannot serialize type: {type(obj)}")


def _to_pretty_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, default=_to_json_dict)


def create_audit_entry(
    user: User, short_description: str, long_description: Optional[dict] = None
) -> AuditLogEntryEntity:
    return AuditLogEntryEntity(
        application=_APPLICATION,
        user=user.username,
        short_description=short_description,
        long_description=_to_pretty_json(long_description)
        if long_description
        else None,
    )
