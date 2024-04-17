"""
Database context.
"""

from typing import Any, Awaitable, TypeVar
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

    def __init__(self, database_url: str, *, echo: bool | None = None):
        self._engine: AsyncEngine = create_async_engine(database_url, echo=echo)
        self.async_session = async_sessionmaker(self._engine)

    async def query_all(  # pylint: disable=too-many-arguments
        self,
        statement: Select,
        *,
        transformer: Callable[[Any], T] | None = None,
        async_transformer: Callable[[Any], Awaitable[T]] | None = None,
        unique: bool = False,
        session: AsyncSession | None = None,
    ) -> Sequence[T]:
        """
        Queries all results for the specified SELECT statement from the database.

        Args:
            statement (Select): a SELECT query
            transformer (Callable[[Any], T], optional): Entity transformer (e.g., DTO factory). Defaults to None.
            async_transformer (Callable[[Any], Awaitable[T]], optional): Async entity transformer (e.g., DTO factory). Defaults to None.
            unique (bool, optional): Whether to return only unique results. Defaults to False.
            session (AsyncSession, optional): Database session to use. Defaults to None, which will make this function use a new session.

        Returns:
            Sequence[T]: Query results
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
        self, entity_class: type, *, session: AsyncSession | None = None
    ) -> int:
        """
        Queries the count for the specified entity class.

        Args:
            entity_class (type): Entity class
            session (AsyncSession, optional): Database session to use. Defaults to None, which will make this function use a new session.

        Returns:
            int: Entity count
        """
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

    async def close(self) -> None:
        """
        Closes the database context.
        """
        await self._engine.dispose()


class _DatabaseContextHolder:
    """
    Database context holder.
    """

    def __init__(self):
        self._context: DatabaseContext | None = None

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
