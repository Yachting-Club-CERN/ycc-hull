"""
Application entry point.
"""
import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ycc_hull.api.boats import api_boats
from ycc_hull.api.holidays import api_holidays
from ycc_hull.api.members import api_members
from ycc_hull.api.test_data import api_test_data
from ycc_hull.config import CONFIG, LOGGING_CONFIG_FILE
from ycc_hull.controllers.members_controller import MembersController

app = FastAPI(
    docs_url="/docs" if CONFIG.api_docs_enabled else None,
    redoc_url="/redoc" if CONFIG.api_docs_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if CONFIG.api_docs_enabled:
    app.swagger_ui_init_oauth = {
        "clientId": CONFIG.keycloak_swagger_client,
        "realm": CONFIG.keycloak_realm,
        # These scopes are needed to be able to use the API.
        "scopes": "openid profile email",
    }

app.include_router(api_boats)
app.include_router(api_holidays)
app.include_router(api_members)

if CONFIG.local:
    app.include_router(api_test_data)


def start() -> None:
    """
    Application entry point.
    """
    print("[init] start() ...")

    # Poke the DB, or fail early if the connection is wrong.
    print("[init] Testing DB connection...")
    membership_types = asyncio.get_event_loop().run_until_complete(
        MembersController.find_all_membership_types()
    )

    print("[init] DB connection successful, membership types: %s", membership_types)

    uvicorn.run(
        "ycc_hull.main:app",
        host="0.0.0.0",
        port=CONFIG.uvicorn_port,
        reload=CONFIG.local,
        log_level="debug",
        log_config=LOGGING_CONFIG_FILE,
    )


if __name__ == "__main__":
    print("[init] main...")
    start()
