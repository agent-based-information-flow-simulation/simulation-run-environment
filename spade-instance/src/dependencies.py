from __future__ import annotations

from typing import Callable

from aiokafka import AIOKafkaProducer
from starlette.requests import Request

from src.kafka import get_app_kafka
from src.state import State, get_app_simulation_state


def create_get_simulation_state() -> Callable[[Request], State]:
    def get_simulation_state(request: Request) -> State:
        return get_app_simulation_state(request.app)

    return get_simulation_state


def create_get_kafka() -> Callable[[Request], AIOKafkaProducer]:
    def get_kafka(request: Request) -> AIOKafkaProducer:
        return get_app_kafka(request.app)

    return get_kafka


state: Callable[[Request], State] = create_get_simulation_state()
kafka: Callable[[Request], AIOKafkaProducer] = create_get_kafka()
