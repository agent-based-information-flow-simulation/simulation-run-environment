from __future__ import annotations

import logging
import os
from multiprocessing import Process
from threading import Lock
from typing import Any, Dict, List, Tuple

from src.exceptions import SimulationException
from src.simulation import main
from src.status import Status

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_STATE", "INFO"))


class State:
    def __init__(self):
        self.mutex: Lock = Lock()
        self.simulation_process: Process | None = None
        self.status: Status = Status.IDLE
        self.num_agents: int = 0
        self.num_alive_agents: int = 0

    def update_active_state(
        self, status: Status, num_agents: int, num_alive_agents: int
    ) -> None:
        logger.debug(f"Setting state: {status}, {num_agents}, {num_alive_agents}")
        with self.mutex:
            if self.status == status.IDLE:
                raise SimulationException(self.status, "Simulation is not running.")
            self.status = status
            self.num_agents = num_agents
            self.num_alive_agents = num_alive_agents

    def get_state(self) -> Tuple[Status, int, int]:
        logger.debug("Getting state")
        with self.mutex:
            return self.status, self.num_agents, self.num_alive_agents

    def start_simulation_process(
        self, agent_code_lines: List[str], agent_data: Dict[str, Any]
    ) -> None:
        logger.debug(f"Starting simulation, state: {self.get_state()}")
        with self.mutex:
            if self.status != Status.IDLE:
                raise SimulationException(self.status, "Simulation is already running.")

            self.status = Status.STARTING
            self.simulation_process = Process(
                target=main, args=(agent_code_lines, agent_data)
            )
            self.simulation_process.start()

    def kill_simulation_process(self) -> None:
        logger.debug(f"Killing simulation, state: {self.get_state()}")
        with self.mutex:
            if self.simulation_process is None:
                raise SimulationException(self.status, "Simulation is not running.")

            self.status = Status.IDLE
            self.num_agents = 0
            self.num_alive_agents = 0
            self.simulation_process.kill()
            self.simulation_process = None


state = State()
