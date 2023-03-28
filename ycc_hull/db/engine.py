"""
DB Engine.
"""
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from ycc_hull.config import DB_ENGINE_ECHO, DB_URL

_ENGINE: Optional[Engine] = None


def _create_db_engine(db_engine_echo: Optional[bool] = None) -> Engine:
    return create_engine(
        DB_URL, echo=DB_ENGINE_ECHO if db_engine_echo is None else db_engine_echo
    )


def get_db_engine() -> Engine:
    global _ENGINE  # pylint: disable=global-statement
    if not _ENGINE:
        _ENGINE = _create_db_engine()
    return _ENGINE
