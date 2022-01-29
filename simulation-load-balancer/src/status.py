from __future__ import annotations

from enum import Enum


class Status(Enum):
    IDLE = "IDLE"
    DEAD = "DEAD"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    ACTIVE = "ACTIVE"
    DEACTIVATED = "DEACTIVATED"
    BROKEN = "BROKEN"
