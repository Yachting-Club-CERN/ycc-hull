from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.exception_handlers import http_exception_handler

from test_data.controllers.test_data_controller import TestDataController
from ycc_hull.api.errors import (
    create_http_error_400,
    create_http_error_404,
    create_http_error_409,
)
from ycc_hull.app_controllers import init_app_controllers
from ycc_hull.auth import auth
from ycc_hull.controllers.errors import (
    ControllerBadRequestError,
    ControllerConflictError,
    ControllerNotFoundError,
)
from ycc_hull.db.context import DatabaseContext, DatabaseContextHolder
from ycc_hull.db.entities import BaseEntity
from ycc_hull.models.user import User

app_test = FastAPI()
init_app_controllers(app_test)


@app_test.exception_handler(ControllerBadRequestError)
async def controller_400_exception_handler(
    request: Request,
    exc: ControllerBadRequestError,
) -> Response:
    return await http_exception_handler(request, create_http_error_400(exc.message))


@app_test.exception_handler(ControllerNotFoundError)
async def controller_404_exception_handler(
    request: Request,
    exc: ControllerNotFoundError,
) -> Response:
    return await http_exception_handler(request, create_http_error_404(exc.message))


@app_test.exception_handler(ControllerConflictError)
async def controller_409_exception_handler(
    request: Request,
    exc: ControllerConflictError,
) -> Response:
    return await http_exception_handler(request, create_http_error_409(exc.message))


class FakeAuth:
    """Mocks app authentication dependency."""

    _member_id: int = -1

    @classmethod
    async def _create_test_user(cls, roles: tuple[str, ...]) -> User:
        return User(
            member_id=cls._member_id,
            username="testuser",
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            groups=(),
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
    async def _create_admin(cls) -> User:
        return await cls._create_test_user(
            roles=(
                "ycc-member-active",
                "ycc-admin",
            )
        )

    @classmethod
    async def _create_committee_member(cls) -> User:
        return await cls._create_test_user(
            roles=(
                "ycc-member-active",
                "ycc-member-committee",
            )
        )

    @classmethod
    def set_member(cls, member_id: int = 100) -> None:
        """Set up auth as a regular member."""
        cls._member_id = member_id
        app_test.dependency_overrides[auth] = cls._create_member

    @classmethod
    def set_helpers_app_admin(cls) -> None:
        """Set up auth as a helpers app admin."""
        cls._member_id = 1
        app_test.dependency_overrides[auth] = cls._create_helpers_app_admin

    @classmethod
    def set_helpers_app_editor(cls) -> None:
        """Set up auth as a helpers app editor."""
        cls._member_id = 2
        app_test.dependency_overrides[auth] = cls._create_helpers_app_editor

    @classmethod
    def set_admin(cls) -> None:
        """Set up auth as an admin."""
        cls._member_id = 1
        app_test.dependency_overrides[auth] = cls._create_admin

    @classmethod
    def set_committee_member(cls) -> None:
        """Set up auth as a committee member."""
        cls._member_id = 1
        app_test.dependency_overrides[auth] = cls._create_committee_member


async def init_test_database(name: str) -> None:
    Path("tmp").mkdir(parents=True, exist_ok=True)  # noqa: ASYNC240
    DatabaseContextHolder.context = DatabaseContext(
        database_url=f"sqlite:///tmp/test-{name}.db", echo=False
    )
    engine = DatabaseContextHolder.context._engine  # noqa: SLF001
    BaseEntity.metadata.drop_all(bind=engine)
    BaseEntity.metadata.create_all(bind=engine)

    await TestDataController().repopulate(add_daily_helper_tasks=False)
