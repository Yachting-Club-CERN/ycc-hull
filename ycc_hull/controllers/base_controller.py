"""
Base controller.
"""
import logging
import re
from abc import ABCMeta
from typing import Any
from sqlalchemy.exc import DatabaseError

from ycc_hull.controllers.exceptions import ControllerConflictException
from ycc_hull.db.context import DatabaseContext, DatabaseContextHolder
from ycc_hull.db.entities import BaseEntity
from ycc_hull.models.base import CamelisedBaseModel
from ycc_hull.models.user import User
from ycc_hull.utils import full_type_name


class BaseController(metaclass=ABCMeta):
    """
    Base controller.
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(full_type_name(self.__class__))

    @property
    def database_context(self) -> DatabaseContext:
        return DatabaseContextHolder.context

    def _handle_database_error(
        self, exc: DatabaseError, what: str, user: User, data: Any
    ) -> Exception:
        self._logger.info(
            "Failed to %s: %s, user: %s, data: %s",
            what,
            exc,
            user,
            data,
        )
        message = str(exc)

        user_message = None
        if "violated - parent key not found" in message:
            if "HELPER_TASKS_CATEGORY_FK" in message:
                user_message = "Invalid category"
            elif "HELPER_TASKS_CONTACT_FK" in message:
                user_message = "Invalid contact"
            elif "HELPER_TASKS_CAPTAIN_REQUIRED_LICENCE_INFO_FK" in message:
                user_message = "Invalid captain required licence info"
        elif "value too large for column" in message:
            # ORA-12899: value too large for column "YCCLOCAL"."HELPER_TASKS"."TITLE" (actual: 69, maximum: 50)\n
            # [SQL: INSERT INTO...
            user_message = "Value too large"
            match = re.search(r"value too large for column\s+([^\s]+)", message)
            if match:
                # Rudimentary solution to at least provide some essential info to the user without
                user_message += ": " + match.group(1).replace('"', "")

        if user_message:
            raise ControllerConflictException(user_message)

        raise exc

    def _update_entity_from_dto(
        self, entity: BaseEntity, request: CamelisedBaseModel
    ) -> None:
        for field, value in request.__dict__.items():
            setattr(entity, field, value)
