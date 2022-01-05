from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.state import Status


class SimulationException(Exception):
    def __init__(self, status: Status, message: str):
        super().__init__(" ".join([f"[status {status}]", message]))
