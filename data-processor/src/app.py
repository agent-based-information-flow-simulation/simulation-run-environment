from __future__ import annotations

from fastapi import FastAPI

from src.routers import router
from src.settings import configure_logging


def get_app(unit_tests: bool = False) -> FastAPI:
    configure_logging()
    app = FastAPI()
    app.include_router(router)

    return app
