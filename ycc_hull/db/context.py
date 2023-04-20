"""
Database context.
"""
from typing import Any, Optional, TypeVar
from collections.abc import Callable, Sequence

from sqlalchemy import Select, create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from ycc_hull.config import CONFIG, Environment

T = TypeVar("T")


class DatabaseContext:
    """
    Database context.
    """

    def __init__(self, database_url: str, echo: Optional[bool] = None) -> None:
        self._engine: Engine = create_engine(database_url, echo=echo)

    def create_session(self) -> Session:
        return Session(self._engine)

    def query_all(
        self,
        statement: Select,
        transformer: Optional[Callable[[Any], T]] = None,
        unique: bool = False,
        session: Optional[Session] = None,
    ) -> Sequence[T]:
        """
        Queries all results for the specified statement from the database.

        Args:
            statement (Select): a SELECT query
            transformer (Callable[[Any], T], optional): Entity transformer (e.g., DTO factory). Defaults to None.

        Returns:
            Sequence[T]: _description_
        """
        transformer_to_use = transformer or (lambda x: x)
        session_to_use = session or self.create_session()

        try:
            result = session_to_use.scalars(statement)
            if unique:
                result = result.unique()

            return [transformer_to_use(row) for row in result]
        finally:
            if not session:
                session_to_use.close()

    def query_count(self, entity_class: type, session: Optional[Session] = None) -> int:
        session_to_use = session or self.create_session()

        try:
            result = session_to_use.scalar(
                select(func.count()).select_from(  # pylint: disable=not-callable
                    entity_class
                )
            )
            if result is None:
                raise AssertionError("COUNT query resulted in None")
            return result
        finally:
            if not session:
                session_to_use.close()


class _DatabaseContextHolder:
    """
    Database context holder.
    """

    def __init__(self) -> None:
        self._context: Optional[DatabaseContext] = None

    @property
    def context(self) -> DatabaseContext:
        if not self._context:
            self._context = DatabaseContext(
                CONFIG.database_url, echo=CONFIG.environment == Environment.LOCAL
            )
        return self._context

    @context.setter
    def context(self, context: DatabaseContext) -> None:
        self._context = context


DatabaseContextHolder = _DatabaseContextHolder()
