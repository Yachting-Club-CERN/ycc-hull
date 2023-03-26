"""
DB Engine.
"""
from sqlalchemy.future import create_engine
from sqlalchemy.future.engine import Engine
from typing import Optional

from ycc_hull.config import DB_URL

_ENGINE: Optional[Engine] = None


def get_db_engine() -> Engine:
    global _ENGINE  # pylint: disable=global-statement
    if not _ENGINE:
        _ENGINE = create_engine(DB_URL, echo=True, future=True)
    return _ENGINE
