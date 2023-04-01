"""
Application entry point.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ycc_hull.api.main import api_main
from ycc_hull.api.test_data import api_test_data

from ycc_hull.config import CORS_ORIGINS, PRODUCTION, UVICORN_PORT, UVICORN_RELOAD


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_main)
if not PRODUCTION:
    app.include_router(api_test_data)


def start() -> None:
    """
    Application entry point.
    """
    uvicorn.run(
        "ycc_hull.main:app", host="0.0.0.0", port=UVICORN_PORT, reload=UVICORN_RELOAD
    )
