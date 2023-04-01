"""
Application entry point.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ycc_hull.api.boats import api_boats
from ycc_hull.api.holidays import api_holidays
from ycc_hull.api.members import api_members
from ycc_hull.api.test_data import api_test_data
from ycc_hull.config import CONFIG, LOGGING_CONFIG_FILE, Environment

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if CONFIG.environment in (Environment.LOCAL, Environment.DEVELOPMENT):
    app.swagger_ui_init_oauth = {
        "clientId": CONFIG.keycloak_swagger_client,
        "realm": CONFIG.keycloak_realm,
        # These scopes are needed to be able to use the API.
        "scopes": "openid profile email",
    }

app.include_router(api_boats)
app.include_router(api_holidays)
app.include_router(api_members)

if CONFIG.is_local:
    app.include_router(api_test_data)


def start() -> None:
    """
    Application entry point.
    """
    uvicorn.run(
        "ycc_hull.main:app",
        host="0.0.0.0",
        port=CONFIG.uvicorn_port,
        reload=CONFIG.is_local,
        log_level="debug",
        log_config=LOGGING_CONFIG_FILE,
    )
