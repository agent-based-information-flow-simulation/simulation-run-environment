from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from src.status import Status


class SimulationException(Exception):
    def __init__(self, status: Status, message: str):
        super().__init__(" ".join([f"[status {status}]", message]))


class SimulationStateNotSetException(Exception):
    def __init__(self):
        super().__init__("Simulation state is not set")


class SimulationIdNotSetException(Exception):
    def __init__(self):
        super().__init__("Simulation id is not set")


class KafkaNotSetException(Exception):
    def __init__(self):
        super().__init__("Kafka is not set")
