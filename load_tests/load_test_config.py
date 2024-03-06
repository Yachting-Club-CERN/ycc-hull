"""
Load test configuration.
"""

from ycc_hull.config import Environment

AUTH_ENVIRONMENT = Environment.DEVELOPMENT

ADMIN_USER = "MHUFF"
OTHER_USER = "TMCDONAL"
API_BASE_URL = "/api/v1"

if AUTH_ENVIRONMENT == Environment.DEVELOPMENT:
    AUTH_URL = "https://ycc-auth.web.cern.ch"
    AUTH_REALM = "YCC-DEV"
    AUTH_CLIENT_ID = "ycc-load-test-dev"
elif AUTH_ENVIRONMENT == Environment.LOCAL:
    AUTH_URL = "https://localhost:8080"
    AUTH_REALM = "YCC-LOCAL"
    AUTH_CLIENT_ID = "ycc-load-test-local"
else:
    raise AssertionError(
        f"Unsupported load testing auth environment: {AUTH_ENVIRONMENT}"
    )
