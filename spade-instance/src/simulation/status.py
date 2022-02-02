from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any, Coroutine, Dict, List

import httpx
import orjson

from src.settings import simulation_settings
from src.status import Status

if TYPE_CHECKING:  # pragma: no cover
    from aioxmpp.structs import JID
    from spade.agent import Agent
    from spade.behaviour import CyclicBehaviour as Behaviour

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_SIMULATION_STATUS", "INFO"))


def get_broken_agents(
    agents: List[Agent],
    agent_behaviours: Dict[JID, List[Behaviour]],
) -> List[str]:
    broken_agents = []

    for agent in agents:
        if (
            not agent
            or not agent.is_alive()
            or not agent.client
            or not agent.client.running
            or not agent.client.established
            or not agent.client.stream
            or not agent.client.stream.running
        ):
            broken_agents.append(str(agent.jid))
            continue

        for behaviour in agent_behaviours[agent.jid]:
            if behaviour._exit_code != 0:
                logger.error(f"[{agent.jid}] {behaviour}: KILLED")
                broken_agents.append(str(agent.jid))
                break

    return broken_agents


def get_instance_status(num_agents: int, broken_agents: List[str]) -> Dict[str, Any]:
    return {
        "status": Status.RUNNING.name,
        "num_agents": num_agents,
        "broken_agents": broken_agents,
    }


async def send_status(
    agents: List[Agent], agent_num_behaviours: Dict[JID, int]
) -> Coroutine[Any, Any, None]:
    broken_agents = get_broken_agents(agents, agent_num_behaviours)
    instance_status = get_instance_status(len(agents), broken_agents)
    logger.info(f"Sending status to spade api: {instance_status}")
    async with httpx.AsyncClient() as client:
        await client.post(
            simulation_settings.status_url,
            headers={"Content-Type": "application/json"},
            data=orjson.dumps(instance_status),
        )
