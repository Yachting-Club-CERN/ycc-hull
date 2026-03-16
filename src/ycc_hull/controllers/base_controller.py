"""Base controller."""

import asyncio
import logging
import re
from abc import ABCMeta
from collections.abc import Coroutine, Generator
from contextlib import contextmanager
from pprint import pformat
from typing import Any

from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import Session

from ycc_hull.controllers.audit import create_audit_entry
from ycc_hull.controllers.exceptions import ControllerConflictError
from ycc_hull.db.context import DatabaseContext, DatabaseContextHolder
from ycc_hull.db.entities import BaseEntity
from ycc_hull.models.base import CamelisedBaseModel
from ycc_hull.models.user import User
from ycc_hull.utils import full_type_name


class BaseController(metaclass=ABCMeta):  # noqa: B024
    """Base controller."""

    def __init__(self) -> None:
        """Initialise the controller."""
        self._logger = logging.getLogger(full_type_name(self.__class__))
        self._background_tasks: set[asyncio.Task] = set()

    @property
    def database_context(self) -> DatabaseContext:
        """Return the shared database context."""
        return DatabaseContextHolder.context

    @contextmanager
    def database_action(
        self,
        *,
        action: str,
        # None is allowed but must be explicit
        user: User | None,
        details: dict[str, Any] | None,
    ) -> Generator[Session, None, None]:
        """Open a database session with error handling."""
        with self.database_context.session() as session:
            try:
                yield session
            except DatabaseError as exc:
                raise self._handle_database_error(  # noqa: B904
                    exc, action=action, user=user, details=details
                )

    def _handle_database_error(  # noqa: C901
        self,
        exc: DatabaseError,
        *,
        action: str,
        user: User | None,
        details: dict[str, Any] | None,
    ) -> Exception:
        if self._logger.isEnabledFor(logging.INFO):
            self._logger.info(
                "Action failed: %s:\n  - Error: %s\n  - User: %s\n  - Details: %s",
                action,
                exc,
                pformat(user),
                pformat(details),
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
            elif "HELPERS_APP_PERMISSIONS_MEMBER_FK" in message:
                user_message = "Invalid member"
        elif "unique constraint" in message and "violated" in message:
            if "HELPERS_APP_PERMISSIONS_PK" in message:
                user_message = "Permission already exists"
        elif "value too large for column" in message:
            # ORA-12899: value too large for column "YCCLOCAL"."HELPER_TASKS"."TITLE"
            # (actual: 69, maximum: 50)\n
            # [SQL: INSERT INTO...
            user_message = "Value too large"
            match = re.search(
                r"value too large for column\s+([^\s]+)",
                message,
            )
            if match:
                # Rudimentary solution to at least provide some essential info to the
                # user without
                user_message += ": " + match.group(1).replace('"', "")

        if user_message:
            raise ControllerConflictError(user_message)

        raise exc

    def _update_entity_from_dto(
        self, entity: BaseEntity, request: CamelisedBaseModel
    ) -> None:
        for field, value in request.__dict__.items():
            setattr(entity, field, value)

    def _audit_log(
        self, session: Session, user: User, description: str, data: dict | None = None
    ) -> None:
        async def wrapper() -> None:
            session.add(create_audit_entry(user, description, data))
            session.commit()

        self._run_in_background(wrapper())

    def _run_in_background(self, coroutine: Coroutine[Any, Any, Any]) -> None:
        async def wrapper() -> None:
            try:
                await coroutine
            except Exception:
                self._logger.exception("Background task failed")

        task = asyncio.create_task(wrapper())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
