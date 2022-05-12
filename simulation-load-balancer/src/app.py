from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.handlers import (
    create_shutdown_redis_connection_handler,
    create_startup_redis_connection_handler,
)
from src.routers import router
from src.settings import configure_logging


def get_app(unit_tests: bool = False) -> FastAPI:
    configure_logging()
    app = FastAPI()

    # accept all orgins as endpoints are only avaialable inside the docker network
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    if not unit_tests:
        app.add_event_handler("startup", create_startup_redis_connection_handler(app))
        app.add_event_handler("shutdown", create_shutdown_redis_connection_handler(app))

    return app
