from __future__ import annotations

import logging
import os
from typing import Any, Coroutine

import httpx
import psutil
from fastapi_utils.tasks import repeat_every

from src.exceptions import SimulationException
from src.settings import instance_settings, simulation_load_balancer_settings
from src.state import state

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_HANDLERS", "INFO"))


async def simulation_shutdown_handler() -> Coroutine[Any, Any, None]:
    logger.info("Shutting down simulation")
    try:
        await state.kill_simulation_process()
    except SimulationException as e:
        logger.info(str(e))
    logger.info("Simulation shutdown complete")


@repeat_every(
    seconds=simulation_load_balancer_settings.announcement_period,
    raise_exceptions=True,
    logger=logger,
)
async def instance_state_handler() -> Coroutine[Any, Any, None]:    
    api_memory_usage = psutil.Process().memory_info().rss / 1024 ** 2
    simulation_memory_usage = await state.get_simulation_memory_usage()
    status, simulation_id, num_agents, broken_agents = await state.get_state()
    instance_state = {
        "status": status.name,
        "simulation_id": simulation_id,
        "num_agents": num_agents,
        "broken_agents": broken_agents,
        "api_memory_usage_MiB": api_memory_usage,
        "simulation_memory_usage_MiB": simulation_memory_usage,
    }
    url = f"{simulation_load_balancer_settings.url}/instances/{instance_settings.id}/state"
    logger.info(f"Sending state to simulation load balancer ({url}): {instance_state}")
    try:
        async with httpx.AsyncClient() as client:
            await client.put(url, json=instance_state)
    except Exception as e:
        logger.warn(f"Error while sending state to simulation load balancer: {e}")
