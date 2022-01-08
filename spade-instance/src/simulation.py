from __future__ import annotations

import asyncio
import copy
import datetime
import logging
import os
import random
from typing import TYPE_CHECKING, Any, Coroutine, Dict, List

import aioxmpp
import httpx
import numpy
import orjson
import spade
from spade.container import Container
import time

from src.settings import (
    backup_settings,
    communication_server_settings,
    instance_settings,
    simulation_settings,
)
from src.status import Status

if TYPE_CHECKING:
    from aioxmpp.structs import JID
    from spade.agent import Agent

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_SIMULATION", "INFO"))


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


# https://github.com/agent-based-information-flow-simulation/spade/blob/6a857c2ae0a86b3bdfd20ccfcd28a11e1c6db81e/spade/agent.py#L171
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


# https://github.com/agent-based-information-flow-simulation/spade/blob/6a857c2ae0a86b3bdfd20ccfcd28a11e1c6db81e/spade/agent.py#L93
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


def connect_agents(agents: List[Agent]) -> None:
    num_connected_agents = 0
    for agent in agents:
        while True:
            try:
                asyncio.run_coroutine_threadsafe(async_connect(agent), loop=Container().loop).result()
            except Exception as e:
                retry_after = simulation_settings.retry_registration_period
                logger.warning(f"[{agent.jid}] Connection error (retry in {retry_after} seconds): {e}")
                time.sleep(retry_after)
                continue
            break
            
        num_connected_agents += 1
        logger.info(f"Connected {num_connected_agents} agents")


# https://github.com/agent-based-information-flow-simulation/spade/blob/6a857c2ae0a86b3bdfd20ccfcd28a11e1c6db81e/spade/agent.py#L137
# setup the agents after they are connected
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


def setup_agents(agents: List[Agent]) -> Dict[JID, int]:
    agent_num_behaviours = {}
    for agent in agents:
        num_behaviours = setup(agent)
        agent_num_behaviours[agent.jid] = num_behaviours

    return agent_num_behaviours


async def send_status(
    agents: List[Agent], agent_num_behaviours: Dict[JID, int]
) -> Coroutine[Any, Any, None]:
    broken_agents = [
        str(agent.jid)
        for agent in agents
        if not agent.is_alive()
        or len(agent.behaviours) != agent_num_behaviours[agent.jid]
    ]
    instance_status = {
        "status": Status.RUNNING.name,
        "num_agents": len(agents),
        "broken_agents": broken_agents,
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
