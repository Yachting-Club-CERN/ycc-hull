"""
Test app & utilities.
"""
import asyncio
import os
from fastapi import FastAPI

from ycc_hull.auth import auth
from ycc_hull.controllers.test_data_controller import TestDataController
from ycc_hull.db.context import DatabaseContext, DatabaseContextHolder
from ycc_hull.db.entities import BaseEntity
from ycc_hull.models.user import User

app_test = FastAPI()


class FakeAuth:
    """
    Mocks app authentication dependency.
    """

    @staticmethod
    async def _create_test_user(roles: tuple[str, ...]) -> User:
        return User(
            member_id=1,
            username="testuser",
            groups=[],
            roles=roles,
        )

    @classmethod
    async def _create_member(cls) -> User:
        return await cls._create_test_user(roles=("ycc-member-active",))

    @classmethod
    async def _create_helpers_app_admin(cls) -> User:
        return await cls._create_test_user(
            roles=(
                "ycc-member-active",
                "ycc-helpers-app-admin",
            )
        )

    @classmethod
    async def _create_helpers_app_editor(cls) -> User:
        return await cls._create_test_user(
            roles=(
                "ycc-member-active",
                "ycc-helpers-app-editor",
            )
        )

    @classmethod
    def set_member(cls) -> None:
        app_test.dependency_overrides[auth] = cls._create_member

    @classmethod
    def set_helpers_app_admin(cls) -> None:
        app_test.dependency_overrides[auth] = cls._create_helpers_app_admin

    @classmethod
    def set_helpers_app_editor(cls) -> None:
        app_test.dependency_overrides[auth] = cls._create_helpers_app_editor


def init_test_database(name: str) -> None:
    if not os.path.exists("tmp"):
        os.makedirs("tmp", exist_ok=True)
    DatabaseContextHolder.context = DatabaseContext(
        database_url=f"sqlite+pysqlite:///tmp/test-{name}.db", echo=True
    )
    engine = DatabaseContextHolder.context._engine  # pylint: disable=protected-access
    BaseEntity.metadata.drop_all(engine)
    BaseEntity.metadata.create_all(engine)

    asyncio.run(TestDataController().repopulate())
