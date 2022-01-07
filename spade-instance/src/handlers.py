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
    try:
        state.kill_simulation_process()
    except SimulationException as e:
        logger.info(str(e))


@repeat_every(
    seconds=simulation_load_balancer_settings.announcement_period,
    raise_exceptions=True,
    logger=logger,
)
async def load_balancer_status_handler() -> Coroutine[Any, Any, None]:
    status, num_agents, num_alive_agents = state.get_state()
    instance_status = {
        "instance_id": instance_settings.id,
        "status": status.name,
        "num_agents": num_agents,
        "num_alive_agents": num_alive_agents,
    }
    logger.info(f"Sending status to simulation load balancer: {instance_status}")
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                simulation_load_balancer_settings.url, json=instance_status
            )
    except Exception as e:
        logger.warn(f"Error sending status to simulation load balancer: {e}")
