from __future__ import annotations

import asyncio
import logging
import os
from multiprocessing import Process
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict, List, Tuple

import psutil
from aioprocessing import AioQueue

from src.exceptions import (
    SimulationException,
    SimulationIdNotSetException,
    SimulationStateNotSetException,
)
from src.kafka import get_app_kafka
from src.settings import kafka_settings
from src.simulation.main import main
from src.status import Status

if TYPE_CHECKING:  # pragma: no cover
    from asyncio.locks import Lock

    from fastapi import FastAPI

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_STATE", "INFO"))


class State:
    def __init__(self, app: FastAPI):
        self.app: FastAPI = app
        self.mutex: Lock = asyncio.Lock()
        self.status: Status = Status.IDLE
        self.simulation_process: Process | None = None
        self.simulation_id: str | None = None
        self.num_agents: int = 0
        self.broken_agents: List[str] = []
        self.agent_updates: AioQueue | None = None
        self.simulation_status_update: AioQueue | None = None

    async def _clean_state(self) -> None:
        # not the most elegant solution
        # it waits for some time for the queues to be empty after the simulation is killed
        # and then it puts poison pills into the queues
        # it's been noticed that sometimes the poison pills are not processed if put immediately
        # TODO: find a better solution
        await self.await_empty_queue(
            self.simulation_status_updates, wait_before_seconds=0.5, every_seconds=0.5
        )
        await self.await_empty_queue(
            self.agent_updates, wait_before_seconds=0.5, every_seconds=0.5
        )
        await self.simulation_status_updates.coro_put(None)
        await self.agent_updates.coro_put(None)

        self.simulation_process = None
        self.simulation_id = None
        self.num_agents = 0
        self.broken_agents = []
        self.agent_updates = None
        self.simulation_status_updates = None

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
            self.agent_updates = AioQueue()
            self.simulation_status_updates = AioQueue()
            self.simulation_process = Process(
                target=main,
                args=(
                    agent_code_lines,
                    agent_data,
                    self.agent_updates,
                    self.simulation_status_updates,
                ),
            )
            self.simulation_process.start()
            asyncio.create_task(
                self.read_update_from_queue_and_run(
                    queue=self.agent_updates,
                    queue_name=f"agent updates ({simulation_id})",
                    simulation_id=simulation_id,
                    func=self.create_send_agent_update_to_broker(),
                )
            )
            asyncio.create_task(
                self.read_update_from_queue_and_run(
                    queue=self.simulation_status_updates,
                    queue_name=f"instance updates ({simulation_id})",
                    simulation_id=self.simulation_id,
                    func=self.create_set_instance_state(),
                )
            )

    def create_send_agent_update_to_broker(self):
        kafka = get_app_kafka(self.app)

        async def send_agent_update_to_broker(
            update: Dict[str, Any], simulation_id: str
        ):
            update["simulation_id"] = simulation_id
            await kafka.send(
                topic=kafka_settings.topic, key=update["jid"], value=update
            )

        return send_agent_update_to_broker

    def create_set_instance_state(self):
        async def set_instance_state(update: Dict[str, Any], simulation_id: str):
            await self.update_active_state(
                status=update["status"],
                num_agents=update["num_agents"],
                broken_agents=update["broken_agents"],
            )

        return set_instance_state

    async def read_update_from_queue_and_run(
        self,
        queue: AioQueue,
        queue_name: str,
        simulation_id: str,
        func: Callable[[Dict[str, Any], str], Coroutine[Any, Any, None]],
    ) -> None:
        queue_size_task = asyncio.create_task(
            self.show_queue_size(queue, every_seconds=30, name=queue_name)
        )

        logger.info(f"Started reading {queue_name} for simulation {simulation_id}")
        while True:
            update: Dict[str, Any] | None = await queue.coro_get()
            if update is None:
                break

            await func(update, simulation_id)

        queue_size_task.cancel()
        logger.info(f"Stopped reading {queue_name} for simulation {simulation_id}")
        logger.info(
            f"Unread items in {queue_name} queue after stopping: {queue.qsize()}"
        )

    async def show_queue_size(
        self, queue: AioQueue, every_seconds: float, name: str
    ) -> None:
        while True:
            logger.info(f"Unread items in {name} queue: {queue.qsize()}")
            await asyncio.sleep(every_seconds)

    async def await_empty_queue(
        self, queue: AioQueue, wait_before_seconds: float, every_seconds: float
    ) -> None:
        await asyncio.sleep(wait_before_seconds)
        while True:
            if queue.empty():
                break
            await asyncio.sleep(every_seconds)

    async def kill_simulation_process(self) -> Coroutine[Any, Any, None]:
        logger.debug(f"Killing simulation, state: {await self.get_state()}")
        async with self.mutex:
            if self.simulation_process is None:
                raise SimulationException(self.status, "Simulation is not running.")

            self.status = Status.IDLE
            self.simulation_process.kill()
            await self._clean_state()

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
                    / 1024**2
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
                await self._clean_state()


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
        set_app_simulation_state(app, State(app))
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
