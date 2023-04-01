"""
DB Engine.
"""
from typing import Any, Callable, Optional, Sequence, TypeVar

from sqlalchemy import Select, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from ycc_hull.config import CONFIG, Environment

_ENGINE: Optional[Engine] = None


def _create_db_engine(db_engine_echo: Optional[bool] = None) -> Engine:
    echo = (
        CONFIG.environment == Environment.LOCAL
        if db_engine_echo is None
        else db_engine_echo
    )
    return create_engine(CONFIG.db_url, echo=echo)


def get_db_engine() -> Engine:
    """
    Gets the database engine. Creates it if it does not exist.

    Returns:
        Engine: the database engine
    """
    global _ENGINE  # pylint: disable=global-statement
    if not _ENGINE:
        _ENGINE = _create_db_engine()
    return _ENGINE


T = TypeVar("T")


def query_all(
    statement: Select, row_transformer: Optional[Callable[[Any], T]] = None
) -> Sequence[T]:
    """
    Queries all results for the specified statement from the database.

    Args:
        statement (Select): a SELECT query
        row_transformer (Callable[[Any], T], optional): Row transformer (e.g., DTO factory). Defaults to None.

    Returns:
        Sequence[T]: _description_
    """
    transformer = row_transformer or (lambda x: x)
    with Session(get_db_engine()) as session:
        return [transformer(row) for row in session.scalars(statement)]


def query_count(entity_class: type) -> int:
    with Session(get_db_engine()) as session:
        return session.query(entity_class).count()
