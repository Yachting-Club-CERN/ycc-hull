"""
Database context.
"""
from typing import Any, Awaitable, Optional, TypeVar
from collections.abc import Callable, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)

from ycc_hull.config import CONFIG, Environment

T = TypeVar("T")


class DatabaseContext:
    """
    Database context.
    """

    def __init__(self, database_url: str, echo: Optional[bool] = None) -> None:
        self._engine: AsyncEngine = create_async_engine(database_url, echo=echo)
        self.async_session = async_sessionmaker(self._engine)

    async def query_all(  # pylint: disable=too-many-arguments
        self,
        statement: Select,
        *,
        transformer: Optional[Callable[[Any], T]] = None,
        async_transformer: Optional[Callable[[Any], Awaitable[T]]] = None,
        unique: bool = False,
        session: Optional[AsyncSession] = None,
    ) -> Sequence[T]:
        """
        Queries all results for the specified statement from the database.

        Args:
            statement (Select): a SELECT query
            transformer (Callable[[Any], T], optional): Entity transformer (e.g., DTO factory). Defaults to None.

        Returns:
            Sequence[T]: _description_
        """
        if transformer and async_transformer:
            raise AssertionError(
                "Only one of transformer and async_transformer can be specified"
            )
        session_to_use = session or self.async_session()

        try:
            result = await session_to_use.scalars(statement)
            if unique:
                result = result.unique()

            if transformer:
                return [transformer(row) for row in result]
            if async_transformer:
                return [await async_transformer(row) for row in result]
            return result.all()
        finally:
            if not session:
                await session_to_use.close()

    async def query_count(
        self, entity_class: type, *, session: Optional[AsyncSession] = None
    ) -> int:
        session_to_use = session or self.async_session()

        try:
            result = await session_to_use.scalar(
                select(func.count()).select_from(  # pylint: disable=not-callable
                    entity_class
                )
            )
            if result is None:
                raise AssertionError("COUNT query resulted in None")
            return result
        finally:
            if not session:
                await session_to_use.close()


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
