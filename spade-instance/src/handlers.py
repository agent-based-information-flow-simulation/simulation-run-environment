from __future__ import annotations

import logging
import os
from typing import Any, Coroutine

import httpx
from fastapi_utils.tasks import repeat_every

from src.exceptions import SimulationException
from src.settings import instance_settings, simulation_load_balancer_settings
from src.state import state

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_HANDLERS", "INFO"))


def simulation_shutdown_handler() -> None:
    logger.info("Shutting down simulation")
    try:
        state.kill_simulation_process()
    except SimulationException as e:
        logger.info(str(e))
    logger.info("Simulation shutdown complete")
    


@repeat_every(
    seconds=simulation_load_balancer_settings.announcement_period,
    raise_exceptions=True,
    logger=logger,
)
async def instance_state_handler() -> Coroutine[Any, Any, None]:
    status, simulation_id, num_agents, num_alive_agents = state.get_state()
    instance_state = {
        "status": status.name,
        "simulation_id": simulation_id,
        "num_agents": num_agents,
        "num_alive_agents": num_alive_agents,
    }
    logger.info(f"Sending state to simulation load balancer: {instance_state}")
    url = f"{simulation_load_balancer_settings.url}/instances/{instance_settings.id}/state"
    try:
        async with httpx.AsyncClient() as client:
            await client.put(url, json=instance_state)
    except Exception as e:
        logger.warn(f"Error while sending state to simulation load balancer: {e}")
