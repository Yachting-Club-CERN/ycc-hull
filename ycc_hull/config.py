import os

PRODUCTION: bool = os.getenv("PRODUCTION") == "1"

UVICORN_PORT: int = 8000
UVICORN_RELOAD: bool = not PRODUCTION


DB_URL: str
if PRODUCTION:
    raise "PRODUCTION IS NOT CONFIGURED"
else:
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
    DB_URL = "oracle+cx_oracle://ycclocal:changeit@127.0.0.1:1521"
