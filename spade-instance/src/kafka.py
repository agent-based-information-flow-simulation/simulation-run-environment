from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Callable, Coroutine

import orjson
from aiokafka import AIOKafkaProducer

from src.exceptions import KafkaNotSetException
from src.settings import kafka_settings

if TYPE_CHECKING:  # pragma: no cover
    from fastapi import FastAPI

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_KAFKA", "INFO"))


def set_app_kafka(app: FastAPI, kafka: AIOKafkaProducer) -> None:
    app.state.kafka = kafka


def get_app_kafka(app: FastAPI) -> AIOKafkaProducer:
    try:
        return app.state.kafka
    except AttributeError:
        raise KafkaNotSetException()


def create_startup_kafka_connection_handler(
    app: FastAPI,
) -> Callable[[], Coroutine[Any, Any, None]]:
    async def connect() -> Coroutine[Any, Any, None]:
        logger.info("Connecting to kafka")
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=kafka_settings.address,
            key_serializer=str.encode,
            value_serializer=orjson.dumps,
        )
        await kafka_producer.start()
        set_app_kafka(app, kafka_producer)
        logger.info("Connected to kafka")

    return connect


def create_shutdown_kafka_connection_handler(
    app: FastAPI,
) -> Callable[[], Coroutine[Any, Any, None]]:
    async def disconnect() -> Coroutine[Any, Any, None]:
        logger.info("Disconnecting from kafka")
        await get_app_kafka(app).stop()
        logger.info("Disconnected from kafka")

    return disconnect
