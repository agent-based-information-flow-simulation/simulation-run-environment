from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from neo4j import AsyncGraphDatabase

from src.settings import database_settings

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_DB_CONNECTION", "INFO"))


def create_startup_db_connection_handler(
    app: FastAPI,
) -> Callable[[], None]:
    def connect() -> None:
        logger.info("Connecting to the database")
        app.state.db_driver = AsyncGraphDatabase.driver(
            database_settings.url, keep_alive=True, max_connection_pool_size=1000
        )
        logger.info("Connected to the database")

    return connect


def create_shutdown_db_connection_handler(
    app: FastAPI,
) -> Callable[[], Coroutine[Any, Any, None]]:
    async def disconnect() -> None:
        logger.info("Disconnecting from the database")
        await app.state.db_driver.close()
        logger.info("Disconnected from the database")

    return disconnect
