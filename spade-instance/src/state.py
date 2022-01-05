from __future__ import annotations

from enum import Enum
from multiprocessing import Process
from threading import Lock
from typing import Any, Dict, List

from src.exceptions import SimulationException
from src.simulation import main


class Status(Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"


class State:
    def __init__(self):
        self.mutex: Lock = Lock()
        self.simulation_process: Process | None = None
        self.status: Status = Status.IDLE

    def get_status(self) -> Status:
        with self.mutex:
            return self.status

    def start_simulation_process(
        self, agent_code_lines: List[str], agent_data: Dict[str, Any]
    ) -> None:
        with self.mutex:
            if self.status != Status.IDLE:
                raise SimulationException(self.status, "Simulation is already running.")

            self.status = Status.RUNNING
            self.simulation_process = Process(
                target=main, args=(agent_code_lines, agent_data)
            )

    def kill_simulation_process(self) -> None:
        with self.mutex:
            if self.simulation_process is None:
                raise SimulationException(self.status, "Simulation is not running.")

            self.status = State.Status.IDLE
            self.simulation_process.kill()
            self.simulation_process = None


state = State()
