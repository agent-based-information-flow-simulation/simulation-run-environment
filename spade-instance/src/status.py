from __future__ import annotations

from enum import Enum


class Status(Enum):
    IDLE = "IDLE"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
