from __future__ import annotations

from contextlib import nullcontext as does_not_raise
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiokafka import AIOKafkaProducer

from src.exceptions import KafkaNotSetException
from src.kafka import (
    create_shutdown_kafka_connection_handler,
    create_startup_kafka_connection_handler,
    get_app_kafka,
    set_app_kafka,
)

if TYPE_CHECKING:
    from fastapi import FastAPI

pytestmark = pytest.mark.asyncio


def test_set_app_kafka_sets_kafka_inside_app_state(app: FastAPI) -> None:
    mocked_kafka = Mock(spec=AIOKafkaProducer)
    app.state.kafka = None

    set_app_kafka(app, mocked_kafka)

    assert app.state.kafka == mocked_kafka


def test_get_app_kafka_returns_kafka_from_app_state(app: FastAPI) -> None:
    mocked_kafka = Mock(spec=AIOKafkaProducer)
    app.state.kafka = mocked_kafka

    returned_kafka = get_app_kafka(app)

    assert returned_kafka == mocked_kafka


def test_get_app_kafka_raises_exception_if_kafka_is_not_set(
    app: FastAPI,
) -> None:
    with pytest.raises(KafkaNotSetException):
        get_app_kafka(app)


async def test_kafka_startup_handler_sets_kafka(
    app: FastAPI,
) -> None:
    with pytest.raises(KafkaNotSetException):
        get_app_kafka(app)

    kafka_startup_handler = create_startup_kafka_connection_handler(app)

    with patch("src.kafka.AIOKafkaProducer", new=AsyncMock):
        await kafka_startup_handler()

    with does_not_raise():
        get_app_kafka(app)


async def test_kafka_shutdown_handler_stops_kafka(
    app: FastAPI,
) -> None:
    mocked_kafka = AsyncMock(spec=AIOKafkaProducer)
    mocked_kafka.stop = AsyncMock()
    set_app_kafka(app, mocked_kafka)

    kafka_shutdown_handler = create_shutdown_kafka_connection_handler(app)
    await kafka_shutdown_handler()

    assert mocked_kafka.stop.called
