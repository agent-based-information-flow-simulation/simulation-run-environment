from __future__ import annotations

import asyncio
import logging
import os
from multiprocessing import Process
from typing import TYPE_CHECKING, Any, Coroutine, Dict, List, Tuple

from src.exceptions import SimulationException
from src.simulation import main
from src.status import Status

if TYPE_CHECKING:
    from asyncio.locks import Lock

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_STATE", "INFO"))


class State:
    def __init__(self):
        self.mutex: Lock = asyncio.Lock()
        self.simulation_process: Process | None = None
        self.simulation_id: str | None = None
        self.status: Status = Status.IDLE
        self.num_agents: int = 0
        self.num_alive_agents: int = 0

    async def update_active_state(
        self, status: Status, num_agents: int, num_alive_agents: int
    ) -> Coroutine[Any, Any, None]:
        logger.debug(f"Setting state: {status}, {num_agents}, {num_alive_agents}")
        async with self.mutex:
            if self.status == status.IDLE:
                raise SimulationException(self.status, "Simulation is not running.")
            self.status = status
            self.num_agents = num_agents
            self.num_alive_agents = num_alive_agents

    async def get_state(self) -> Coroutine[Any, Any, Tuple[Status, str, int, int]]:
        logger.debug("Getting state")
        async with self.mutex:
            return (
                self.status,
                self.simulation_id,
                self.num_agents,
                self.num_alive_agents,
            )

    async def get_simulation_id(self) -> Coroutine[Any, Any, str]:
        logger.debug("Getting simulation id")
        async with self.mutex:
            return self.simulation_id

    async def start_simulation_process(
        self,
        simulation_id: str,
        agent_code_lines: List[str],
        agent_data: Dict[str, Any],
    ) -> Coroutine[Any, Any, None]:
        logger.debug(
            f"Starting simulation {simulation_id}, state: {await self.get_state()}"
        )
        async with self.mutex:
            if self.status != Status.IDLE:
                raise SimulationException(self.status, "Simulation is already running.")

            self.status = Status.STARTING
            self.simulation_id = simulation_id
            self.simulation_process = Process(
                target=main, args=(agent_code_lines, agent_data)
            )
            self.simulation_process.start()

    async def kill_simulation_process(self) -> Coroutine[Any, Any, None]:
        logger.debug(f"Killing simulation, state: {await self.get_state()}")
        async with self.mutex:
            if self.simulation_process is None:
                raise SimulationException(self.status, "Simulation is not running.")

            self.status = Status.IDLE
            self.simulation_id = None
            self.num_agents = 0
            self.num_alive_agents = 0
            self.simulation_process.kill()
            self.simulation_process = None


state = State()
