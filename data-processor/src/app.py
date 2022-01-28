from __future__ import annotations

from fastapi import FastAPI

from src.db.connection import (
    create_shutdown_db_connection_handler,
    create_startup_db_connection_handler,
)
from src.routers.backup import router as backup_router
from src.routers.statistics import router as statistics_router
from src.settings import configure_logging


def get_app(unit_tests: bool = False) -> FastAPI:
    configure_logging()

    app = FastAPI()
    app.include_router(backup_router)
    app.include_router(statistics_router)

    if not unit_tests:
        app.add_event_handler("startup", create_startup_db_connection_handler(app))
        app.add_event_handler("shutdown", create_shutdown_db_connection_handler(app))

    return app
