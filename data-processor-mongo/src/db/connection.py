from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from motor.motor_asyncio import AsyncIOMotorClient

from src.settings import database_settings

if TYPE_CHECKING:
    from typing import Callable

    from fastapi import FastAPI


logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_DB_CONNECTION", "INFO"))


def create_startup_db_connection_handler(
    app: FastAPI,
) -> Callable[[], None]:
    def connect() -> None:
        logger.info("Connecting to the database")
        app.state.db_client = AsyncIOMotorClient(database_settings.url)
        logger.info("Connected to the database")

    return connect


def create_shutdown_db_connection_handler(
    app: FastAPI,
) -> Callable[[], None]:
    def disconnect() -> None:
        logger.info("Disconnecting from the database")
        app.state.db_client.close()
        logger.info("Disconnected from the database")

    return disconnect


def create_startup_db_access_handler(
    app: FastAPI,
) -> Callable[[], None]:
    def access_db() -> None:
        logger.info("Accessing the database")
        app.state.db = app.state.db_client.get_database("simulations")
        logger.info("Accessed the database")

    return access_db
