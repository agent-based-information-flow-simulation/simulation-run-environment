from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Coroutine

import aioredis

from src.settings import redis_settings

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_HANDLERS", "INFO"))


def create_startup_redis_connection_handler(
    app: FastAPI,
) -> Callable[[], Awaitable[None]]:
    async def connect_redis():
        logger.info("Connecting to redis...")
        app.state.redis = await aioredis.Redis(
            host=redis_settings.redis_address,
            port=redis_settings.redis_port,
            password=redis_settings.redis_password,
        )
        logger.info("Connected to redis")
        logger.info("Flushing all keys...")
        for key in await app.state.redis.keys("*"):
            await app.state.redis.delete(key)
        logger.info("Flushed all keys")
        logger.info("Setting up redis complete")

    return connect_redis


def create_shutdown_redis_connection_handler(
    app: FastAPI,
) -> Callable[[], Awaitable[None]]:
    async def disconnect_redis():
        logger.info("Disconnecting from redis")
        await app.state.redis.close()
        logger.info("Disconnected from redis")

    return disconnect_redis
