from __future__ import annotations

from fastapi import FastAPI

from src.handlers import (
    create_instance_state_handler,
    create_simulation_process_health_check_handler,
    create_simulation_state_shutdown_handler,
    create_simulation_state_startup_handler,
)
from src.routers import router
from src.settings import configure_logging


def get_app(unit_tests: bool = False) -> FastAPI:
    configure_logging()

    app = FastAPI()
    app.include_router(router)

    if not unit_tests:  # pragma: no cover
        app.add_event_handler("startup", create_simulation_state_startup_handler(app))
        app.add_event_handler("startup", create_instance_state_handler(app))
        app.add_event_handler(
            "startup", create_simulation_process_health_check_handler(app)
        )
        app.add_event_handler("shutdown", create_simulation_state_shutdown_handler(app))

    return app
