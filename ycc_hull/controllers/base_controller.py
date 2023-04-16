"""
Base controller.
"""
from abc import ABCMeta

from ycc_hull.db.context import DatabaseContext, DatabaseContextHolder


class BaseController(metaclass=ABCMeta):
    """
    Base controller.
    """

    @property
    def database_context(self) -> DatabaseContext:
        return DatabaseContextHolder.context
