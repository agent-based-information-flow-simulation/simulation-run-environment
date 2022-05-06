from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from src.db.connection import (
    create_shutdown_db_connection_handler,
    create_startup_db_access_handler,
    create_startup_db_connection_handler,
)
from src.routers.timeseries import router as timeseries_router
from src.settings import configure_logging


def get_app(unit_tests: bool = False) -> FastAPI:
    configure_logging()

    app = FastAPI()
    app.include_router(timeseries_router)

    if not unit_tests:
        app.add_event_handler("startup", create_startup_db_connection_handler(app))
        app.add_event_handler("shutdown", create_shutdown_db_connection_handler(app))
        app.add_event_handler("startup", create_startup_db_access_handler(app))

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    return app
