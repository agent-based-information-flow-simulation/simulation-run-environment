from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict

import httpx
import psutil
from fastapi_utils.tasks import repeat_every

from src.exceptions import SimulationException
from src.settings import instance_settings, simulation_load_balancer_settings
from src.state import State, get_app_simulation_state, set_app_simulation_state

if TYPE_CHECKING:  # pragma: no cover
    from fastapi import FastAPI

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_HANDLERS", "INFO"))


def create_simulation_state_startup_handler(app: FastAPI) -> Callable[[], None]:
    def simulation_state_startup_handler() -> None:
        logger.info("Setting up simulation state")
        set_app_simulation_state(app, State())
        logger.info("Simulation state set up complete")

    return simulation_state_startup_handler


def create_simulation_state_shutdown_handler(
    app: FastAPI,
) -> Callable[[], Awaitable[None]]:
    async def simulation_state_shutdown_handler() -> Awaitable[None]:
        logger.info("Shutting down simulation")
        try:
            await get_app_simulation_state(app).kill_simulation_process()
        except SimulationException as e:
            logger.info(str(e))
        logger.info("Simulation shutdown complete")

    return simulation_state_shutdown_handler


async def get_instance_information(app: FastAPI) -> Awaitable[Dict[str, Any]]:
    api_memory_usage = psutil.Process().memory_info().rss / 1024 ** 2
    simulation_memory_usage = await get_app_simulation_state(
        app
    ).get_simulation_memory_usage()
    status, simulation_id, num_agents, broken_agents = await get_app_simulation_state(
        app
    ).get_state()
    return {
        "status": status.name,
        "simulation_id": simulation_id,
        "num_agents": num_agents,
        "broken_agents": broken_agents,
        "api_memory_usage_MiB": api_memory_usage,
        "simulation_memory_usage_MiB": simulation_memory_usage,
    }


def create_instance_state_handler(app: FastAPI) -> Callable[[], Awaitable[None]]:
    @repeat_every(
        seconds=simulation_load_balancer_settings.announcement_period,
        raise_exceptions=False,
        logger=logger,
    )
    async def instance_state_handler() -> Awaitable[None]:
        instance_state = await get_instance_information(app)
        url = f"{simulation_load_balancer_settings.url}/instances/{instance_settings.id}/state"
        logger.info(
            f"Sending state to simulation load balancer ({url}): {instance_state}"
        )
        try:
            async with httpx.AsyncClient() as client:
                await client.put(url, json=instance_state)
        except Exception as e:
            logger.warn(f"Error while sending state to simulation load balancer: {e}")

    return instance_state_handler


def create_simulation_process_health_check_handler(
    app: FastAPI,
) -> Callable[[], Awaitable[None]]:
    @repeat_every(
        seconds=instance_settings.process_health_check_period,
        raise_exceptions=False,
        logger=logger,
    )
    async def simulation_process_health_check_handler() -> Awaitable[None]:
        await get_app_simulation_state(app).verify_simulation_process()

    return simulation_process_health_check_handler
