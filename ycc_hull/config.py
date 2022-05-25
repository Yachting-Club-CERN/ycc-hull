import os

PRODUCTION: bool = os.getenv("PRODUCTION") == "1"

UVICORN_PORT: int = 8000
UVICORN_RELOAD: bool = not PRODUCTION

DB_URL: str
if PRODUCTION:
    raise "PRODUCTION IS NOT CONFIGURED"
else:
    DB_URL = "oracle+cx_oracle://ycclocal:changeit@127.0.0.1:1521"
