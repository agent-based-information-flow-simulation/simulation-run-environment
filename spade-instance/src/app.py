from __future__ import annotations

from fastapi import FastAPI

from src.kafka import (
    create_shutdown_kafka_connection_handler,
    create_startup_kafka_connection_handler,
)
from src.repeated_tasks import (
    create_instance_state_handler,
    create_simulation_process_health_check_handler,
)
from src.routers import router
from src.settings import configure_logging
from src.state import (
    create_simulation_state_shutdown_handler,
    create_simulation_state_startup_handler,
)


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
        app.add_event_handler("startup", create_startup_kafka_connection_handler(app))
        app.add_event_handler("shutdown", create_simulation_state_shutdown_handler(app))
        app.add_event_handler("shutdown", create_shutdown_kafka_connection_handler(app))

    return app
