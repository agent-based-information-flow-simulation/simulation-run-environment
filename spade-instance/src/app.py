from __future__ import annotations

from fastapi import FastAPI

from src.handlers import load_balancer_status_handler, simulation_shutdown_handler
from src.routers import router


def get_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    app.add_event_handler("startup", load_balancer_status_handler)
    app.add_event_handler("shutdown", simulation_shutdown_handler)
    return app
