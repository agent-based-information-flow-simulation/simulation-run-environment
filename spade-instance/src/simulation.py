import asyncio
import copy
import datetime
import json
import logging
import os
import random
from typing import Any, Coroutine, Dict, List

import aioxmpp
import httpx
import numpy
import spade
from spade.agent import Agent
from spade.container import Container

from src.settings import (
    backup_settings,
    communication_server_settings,
    instance_settings,
    simulation_settings,
)
from src.status import Status

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_SIMULATION", "INFO"))


# TLS is set to false
async def async_register(agent: Agent) -> Coroutine[Any, Any, None]:
    metadata = aioxmpp.make_security_layer(
        None, no_verify=not agent.verify_security
    )._replace(tls_required=False)
    query = aioxmpp.ibr.Query(agent.jid.localpart, agent.password)
    _, stream, _ = await aioxmpp.node.connect_xmlstream(
        agent.jid, metadata, loop=agent.loop
    )
    await aioxmpp.ibr.register(stream, query)


# TLS is set to false
# register and connect client
async def async_connect(agent: Agent) -> Coroutine[Any, Any, None]:
    await agent._hook_plugin_before_connection()
    await async_register(agent)
    agent.client = aioxmpp.PresenceManagedClient(
        agent.jid,
        aioxmpp.make_security_layer(
            agent.password, no_verify=not agent.verify_security
        )._replace(tls_required=False),
        loop=agent.loop,
        logger=logging.getLogger(agent.jid.localpart),
    )
    agent.message_dispatcher = agent.client.summon(
        aioxmpp.dispatcher.SimpleMessageDispatcher
    )
    agent.presence = spade.presence.PresenceManager(agent)
    await agent._async_connect()
    agent.message_dispatcher.register_callback(
        aioxmpp.MessageType.CHAT,
        None,
        agent._message_received,
    )
    await agent._hook_plugin_after_connection()


# separate function to setup the agents after they are connected
def setup(agent: Agent) -> int:
    agent.setup()
    agent._alive.set()
    num_behaviours = len(agent.behaviours)

    for behaviour in agent.behaviours:
        if not behaviour.is_running:
            behaviour.set_agent(agent)
            if issubclass(type(behaviour), spade.behaviour.FSMBehaviour):
                for _, state in behaviour.get_states().items():
                    state.set_agent(agent)
            behaviour.start()

    return num_behaviours


def initialize_agents(
    agent_code_lines: List[str], agent_data: List[Dict[str, Any]]
) -> List[Agent]:
    code_without_imports = list(
        filter(lambda line: not line.startswith("import"), agent_code_lines)
    )
    exec("\n".join(code_without_imports))

    agents = []
    for agent_data_dict in agent_data:
        agent_type = agent_data_dict["type"]
        del agent_data_dict["type"]
        agent = locals()[agent_type](
            password=communication_server_settings.password,
            backup_url=backup_settings.agent_backup_url,
            backup_period=backup_settings.period,
            backup_delay=backup_settings.delay,
            logger=logger,
            **agent_data_dict,
        )
        agents.append(agent)

    return agents


def connect_agents(agents: List[Agent]) -> None:
    num_concurrent_connections = min(
        len(agents), simulation_settings.num_concurrent_registration
    )
    for agent in zip(*[iter(agents)] * num_concurrent_connections):
        futures = [
            asyncio.run_coroutine_threadsafe(
                async_connect(agent), loop=Container().loop
            )
            for agent in agent
        ]
        for future in futures:
            future.result()


def setup_agents(agents: List[Agent]) -> Dict[str, int]:
    agent_num_behaviours = {}
    for agent in agents:
        num_behaviours = setup(agent)
        agent_num_behaviours[agent.jid] = num_behaviours

    return agent_num_behaviours


async def send_status(
    agents: List[Agent], agent_num_behaviours: Dict[str, int]
) -> Coroutine[Any, Any, None]:
    num_alive_agents = sum(
        agent.is_alive() and len(agent.behaviours) == agent_num_behaviours[agent.jid]
        for agent in agents
    )

    instance_status = {
        "status": Status.RUNNING.name,
        "num_alive_agents": num_alive_agents,
        "num_agents": len(agents),
    }
    logger.info(f"Sending status to spade api: {instance_status}")
    async with httpx.AsyncClient() as client:
        await client.post(instance_settings.status_url, json=instance_status)


async def run_simulation(
    agent_code_lines: List[str], agent_data: List[Dict[str, Any]]
) -> Coroutine[Any, Any, None]:
    logger.info("Initializing agents...")
    agents = initialize_agents(agent_code_lines, agent_data)

    logger.info("Connecting agents to the communication server...")
    connect_agents(agents)

    logger.info("Running setup...")
    agent_num_behaviours = setup_agents(agents)

    logger.info(f"Simulation started with {len(agents)} agents.")
    while True:
        Container().reset()
        await send_status(agents, agent_num_behaviours)
        await asyncio.sleep(10)


def main(agent_code_lines: List[str], agent_data: List[Dict[str, Any]]) -> None:
    asyncio.run(run_simulation(agent_code_lines, agent_data))
