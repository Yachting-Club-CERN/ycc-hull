"""
Application configuration.
"""
import os

PRODUCTION: bool = os.getenv("PRODUCTION") == "1"

UVICORN_PORT: int = 8000
UVICORN_RELOAD: bool = not PRODUCTION

DB_ENGINE_ECHO: bool
DB_URL: str

if PRODUCTION:
    # DB URL format: oracle+oracledb://user:pass@hostname:port[/dbname][?service_name=<service>[&key=value&key=value...]]
    raise Exception("PRODUCTION IS NOT CONFIGURED")
else:
    DB_ENGINE_ECHO = True
    CORS_ORIGINS = [
        "http://localhost:3000",
        "localhost:3000",
        "http://127.0.0.1:3000",
        "127.0.0.1:3000",
        "http://localhost:8080",
        "localhost:8080",
        "http://127.0.0.1:8080",
        "127.0.0.1:8080",
    ]
    # DB_URL = "oracle+oracledb://ycclocal:changeit@127.0.0.1:1521"
    # This below works, no idea why the one above does not
    DB_URL = "oracle+oracledb://ycclocal:changeit@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=127.0.0.1)(PORT=1521)))"
