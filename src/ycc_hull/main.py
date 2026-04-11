"""Application entry point."""

import locale
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import toml
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from ycc_hull.api.audit_log import api_audit_log
from ycc_hull.api.boats import api_boats
from ycc_hull.api.errors import (
    create_http_error_400,
    create_http_error_404,
    create_http_error_409,
)
from ycc_hull.api.helpers import api_helpers
from ycc_hull.api.holidays import api_holidays
from ycc_hull.api.licences import api_licences
from ycc_hull.api.members import api_members
from ycc_hull.app_controllers import (
    get_controllers,
    init_app_controllers,
)
from ycc_hull.config import CONFIG
from ycc_hull.constants import LOGGING_CONFIG_FILE
from ycc_hull.controllers.errors import (
    ControllerBadRequestError,
    ControllerConflictError,
    ControllerNotFoundError,
)
from ycc_hull.db.context import DatabaseContextHolder
from ycc_hull.scheduler import init_scheduler

_logger = logging.getLogger(__name__)

locale.setlocale(locale.LC_ALL, "en_GB.UTF-8")


def read_version_from_pyproject_toml() -> str:
    """Read the version from the pyproject.toml file."""
    for project_dir in ["../", "../../"]:
        pyproject_toml_file = (
            Path(__file__).parent / project_dir / "pyproject.toml"
        ).resolve()
        if pyproject_toml_file.exists():
            with pyproject_toml_file.open(encoding="utf-8") as file:
                return toml.load(file)["project"]["version"]

    msg = "pyproject.toml not found"
    raise FileNotFoundError(msg)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    # Poke the DB or fail early if the connection is wrong
    init_app_controllers(fastapi_app)

    _logger.info("Startup event received, testing DB connection...")
    membership_types = await get_controllers(
        fastapi_app
    ).members_controller.find_all_membership_types()
    _logger.info("DB connection successful, membership types: %s", membership_types)

    _logger.info("Starting the scheduler")
    scheduler = init_scheduler(fastapi_app)
    scheduler.start()

    yield

    _logger.info("Shutdown event received, closing DB connection...")
    await DatabaseContextHolder.context.close()
    _logger.info("Stopping the scheduler...")
    scheduler.shutdown()


app = FastAPI(
    title="YCC Hull",
    description="Federated YCC API. Enjoy! 🐨",
    version=f"{read_version_from_pyproject_toml()}-{CONFIG.environment.value}",
    docs_url="/docs" if CONFIG.api_docs_enabled else None,
    redoc_url="/redoc" if CONFIG.api_docs_enabled else None,
    lifespan=lifespan,
)


@app.exception_handler(ControllerBadRequestError)
async def controller_400_exception_handler(
    request: Request,
    exc: ControllerBadRequestError,
) -> Response:
    """Handle 400 Bad Request exceptions."""
    return await http_exception_handler(request, create_http_error_400(exc.message))


@app.exception_handler(ControllerNotFoundError)
async def controller_404_exception_handler(
    request: Request,
    exc: ControllerNotFoundError,
) -> Response:
    """Handle 404 Not Found exceptions."""
    return await http_exception_handler(request, create_http_error_404(exc.message))


@app.exception_handler(ControllerConflictError)
async def controller_409_exception_handler(
    request: Request,
    exc: ControllerConflictError,
) -> Response:
    """Handle 409 Conflict exceptions."""
    return await http_exception_handler(request, create_http_error_409(exc.message))


app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.cors_origins,  # ty: ignore[invalid-argument-type]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if CONFIG.api_docs_enabled:
    app.swagger_ui_init_oauth = {
        "clientId": CONFIG.keycloak.swagger_client,
        "realm": CONFIG.keycloak.realm,
        # These scopes are needed to be able to use the API.
        "scopes": "openid profile email",
    }


@app.get("/", response_class=HTMLResponse)
async def landing_page() -> str:
    """Landing page that redirects to the club website."""
    club_website = "https://yachting.web.cern.ch/"
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url={club_website}" />
    <script>window.location.href = "{club_website}";</script>
    <title>YCC Hull</title>
</head>
<body>
    <p>Redirecting to <a href="{club_website}">YCC website</a>...</p>
</body>
</html>"""


app.include_router(api_audit_log)
app.include_router(api_boats)
app.include_router(api_helpers)
app.include_router(api_holidays)
app.include_router(api_licences)
app.include_router(api_members)

if CONFIG.local:
    from test_data.api.test_data import api_test_data

    app.include_router(api_test_data)


def main() -> None:
    """Application entry point."""
    Path("log").mkdir(parents=True, exist_ok=True)

    # This must be in a sync function
    uvicorn.run(
        "ycc_hull.main:app",
        host="0.0.0.0",  # noqa: S104
        port=CONFIG.uvicorn_port,
        reload=CONFIG.local,
        log_level="debug",
        log_config=str(LOGGING_CONFIG_FILE),
    )


if __name__ == "__main__":
    main()
