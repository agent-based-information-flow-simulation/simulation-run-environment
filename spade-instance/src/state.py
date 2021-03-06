from __future__ import annotations

import asyncio
import logging
import os
from multiprocessing import Process
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict, List, Tuple

import psutil

from src.exceptions import (
    SimulationException,
    SimulationIdNotSetException,
    SimulationStateNotSetException,
)
from src.simulation.main import main
from src.status import Status

if TYPE_CHECKING:  # pragma: no cover
    from asyncio.locks import Lock

    from fastapi import FastAPI

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_STATE", "INFO"))


class State:
    def __init__(self):
        self.mutex: Lock = asyncio.Lock()
        self.status: Status = Status.IDLE
        self.simulation_process: Process | None = None
        self.simulation_id: str | None = None
        self.num_agents: int = 0
        self.broken_agents: List[str] = []

    def _clean_state(self) -> None:
        self.simulation_process = None
        self.simulation_id = None
        self.num_agents = 0
        self.broken_agents = []

    async def update_active_state(
        self, status: Status, num_agents: int, broken_agents: List[str]
    ) -> Coroutine[Any, Any, None]:
        logger.debug(f"Setting state: {status}, {num_agents}, {broken_agents}")
        async with self.mutex:
            if self.status == status.IDLE:
                raise SimulationException(self.status, "Simulation is not running.")

            self.status = status
            self.num_agents = num_agents
            self.broken_agents = broken_agents

    async def get_state(
        self,
    ) -> Coroutine[Any, Any, Tuple[Status, str, int, List[str]]]:
        logger.debug("Getting state")
        async with self.mutex:
            return (
                self.status,
                self.simulation_id,
                self.num_agents,
                self.broken_agents,
            )

    async def get_simulation_id(self) -> Coroutine[Any, Any, str]:
        logger.debug("Getting simulation id")
        async with self.mutex:
            if self.simulation_id is None:
                raise SimulationIdNotSetException()

            return self.simulation_id

    async def start_simulation_process(
        self,
        simulation_id: str,
        agent_code_lines: List[str],
        agent_data: List[Dict[str, Any]],
    ) -> Coroutine[Any, Any, None]:
        logger.debug(
            f"Starting simulation {simulation_id}, state: {await self.get_state()}"
        )
        async with self.mutex:
            if self.status not in (Status.IDLE, Status.DEAD):
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
            self.simulation_process.kill()
            self._clean_state()

    async def get_simulation_memory_usage(self) -> Coroutine[Any, Any, float]:
        logger.debug(
            f"Getting simulation memory usage, state: {await self.get_state()}"
        )
        async with self.mutex:
            if (
                self.simulation_process is not None
                and self.simulation_process.is_alive()
            ):
                return (
                    psutil.Process(self.simulation_process.pid).memory_info().rss
                    / 1024 ** 2
                )

            return 0.0

    async def verify_simulation_process(self) -> Coroutine[Any, Any, None]:
        logger.debug(f"Verify simulation process, state: {await self.get_state()}")
        async with self.mutex:
            if (
                self.simulation_process is not None
                and not self.simulation_process.is_alive()
            ):
                logger.warning("Simulation process is dead")
                self.status = Status.DEAD
                self._clean_state()


def set_app_simulation_state(app: FastAPI, state: State) -> None:
    app.state.simulation_state = state


def get_app_simulation_state(app: FastAPI) -> State:
    try:
        return app.state.simulation_state
    except AttributeError:
        raise SimulationStateNotSetException()


def create_simulation_state_startup_handler(app: FastAPI) -> Callable[[], None]:
    def simulation_state_startup_handler() -> None:
        logger.info("Setting up simulation state")
        set_app_simulation_state(app, State())
        logger.info("Simulation state set up complete")

    return simulation_state_startup_handler


def create_simulation_state_shutdown_handler(
    app: FastAPI,
) -> Callable[[], Coroutine[Any, Any, None]]:
    async def simulation_state_shutdown_handler() -> Coroutine[Any, Any, None]:
        logger.info("Shutting down simulation")
        try:
            await get_app_simulation_state(app).kill_simulation_process()
        except SimulationException as e:
            logger.info(str(e))
        logger.info("Simulation shutdown complete")

    return simulation_state_shutdown_handler
