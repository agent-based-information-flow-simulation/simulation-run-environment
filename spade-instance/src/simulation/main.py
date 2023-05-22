from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any, Coroutine, Dict, List

import spade
import uvloop
from spade.container import Container

from src.settings import simulation_settings
from src.simulation.code_generation import generate_agents
from src.simulation.initialization import connect_agents, setup_agents
from src.simulation.status import send_status

if TYPE_CHECKING:  # pragma: no cover
    from aioprocessing import AioQueue
    from aioxmpp.structs import JID
    from spade.agent import Agent

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_SIMULATION_MAIN", "INFO"))
logging.getLogger("spade.behaviour").setLevel(
    level=os.environ.get("LOG_LEVEL_SPADE_BEHAVIOUR", "WARNING")
)


class SimulationInfiniteLoop:
    RUNNING = True

    async def run(
        self,
        agents: List[Agent],
        agent_behaviours: Dict[JID, List[spade.behaviour.PeriodicBehaviour]],
        status_annoucement_period: int,
        simulation_status_updates: AioQueue,
    ) -> Coroutine[Any, Any, None]:
        while self.RUNNING:
            Container().reset()
            await send_status(agents, agent_behaviours, simulation_status_updates)
            await asyncio.sleep(status_annoucement_period)


async def run_simulation(
    agent_code_lines: List[str],
    agent_data: List[Dict[str, Any]],
    agent_updates: AioQueue,
    simulation_status_updates: AioQueue,
) -> Coroutine[Any, Any, None]:
    Container().loop = asyncio.get_running_loop()

    logger.info("Generating agents...")
    agents = generate_agents(agent_code_lines, agent_data, agent_updates)

    logger.info("Connecting agents to the communication server...")
    await connect_agents(agents)

    logger.info("Running setup...")
    agent_behaviours = setup_agents(agents)

    logger.info(f"Simulation started with {len(agents)} agents.")
    await SimulationInfiniteLoop().run(
        agents,
        agent_behaviours,
        simulation_settings.status_period,
        simulation_status_updates,
    )


def main(
    agent_code_lines: List[str],
    agent_data: List[Dict[str, Any]],
    agent_updates: AioQueue,
    simulation_status_updates: AioQueue,
) -> None:
    uvloop.install()
    asyncio.run(
        run_simulation(
            agent_code_lines, agent_data, agent_updates, simulation_status_updates
        )
    )
