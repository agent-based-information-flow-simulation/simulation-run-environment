from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING, Any, Coroutine, Dict, List

import aioxmpp
from spade.behaviour import FSMBehaviour
from spade.presence import PresenceManager

from src.settings import simulation_settings

if TYPE_CHECKING:  # pragma: no cover
    from aioxmpp.structs import JID
    from spade.agent import Agent
    from spade.behaviour import CyclicBehaviour as Behaviour

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_SIMULATION_INITIALIZATION", "INFO"))


# https://github.com/agent-based-information-flow-simulation/spade/blob/6a857c2ae0a86b3bdfd20ccfcd28a11e1c6db81e/spade/agent.py#L171
# TLS is set to false
async def async_register(agent: Agent) -> Coroutine[Any, Any, None]:  # pragma: no cover
    metadata = aioxmpp.make_security_layer(
        None, no_verify=not agent.verify_security
    )._replace(tls_required=False)
    query = aioxmpp.ibr.Query(agent.jid.localpart, agent.password)
    _, stream, _ = await aioxmpp.node.connect_xmlstream(
        agent.jid, metadata, loop=agent.loop
    )
    setattr(agent, "xml_stream", stream)
    await aioxmpp.ibr.register(stream, query)


# https://github.com/agent-based-information-flow-simulation/spade/blob/6a857c2ae0a86b3bdfd20ccfcd28a11e1c6db81e/spade/agent.py#L93
# TLS is set to false
# register and connect client
async def async_connect(agent: Agent) -> Coroutine[Any, Any, None]:  # pragma: no cover
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
    agent.presence = PresenceManager(agent)
    await agent._async_connect()
    agent.message_dispatcher.register_callback(
        aioxmpp.MessageType.CHAT,
        None,
        agent._message_received,
    )
    await agent._hook_plugin_after_connection()


async def connect_with_retry(
    agent: Agent, retry_after: int
) -> Coroutine[Any, Any, None]:
    while True:
        logger.debug(f"Attempting to connect agent {agent.jid}")
        try:
            await async_connect(agent)
        except Exception as e:
            logger.warning(
                f"[{agent.jid}] Connection error (retry in {retry_after} seconds): {e}"
            )
            await asyncio.sleep(retry_after)
            continue
        break
    logger.info(f"[{agent.jid}] Connected")


async def connect_agents(agents: List[Agent]) -> Coroutine[Any, Any, None]:
    concurrency = simulation_settings.registration_max_concurrency
    semaphore = asyncio.Semaphore(concurrency)

    logger.debug(f"Connecting agents with concurrency {concurrency}")

    async def rate_limited_connect(agent: Agent) -> Coroutine[Any, Any, None]:
        async with semaphore:
            await connect_with_retry(
                agent, simulation_settings.registration_retry_after
            )

    tasks = [asyncio.create_task(rate_limited_connect(agent)) for agent in agents]
    await asyncio.gather(*tasks)


# https://github.com/agent-based-information-flow-simulation/spade/blob/6a857c2ae0a86b3bdfd20ccfcd28a11e1c6db81e/spade/agent.py#L137
# setup agent after it has been connected
def setup_agent(agent: Agent) -> List[Behaviour]:
    import copy

    agent.setup()
    agent._alive.set()
    behaviours = copy.copy(agent.behaviours)

    logger.debug(f"Agent {agent.jid} behaviours: {behaviours}")

    for behaviour in agent.behaviours:  # pragma: no cover
        if not behaviour.is_running:
            behaviour.set_agent(agent)
            if issubclass(type(behaviour), FSMBehaviour):
                for _, state in behaviour.get_states().items():
                    state.set_agent(agent)
            behaviour.start()

    return behaviours


def setup_agents(agents: List[Agent]) -> Dict[JID, List[Behaviour]]:
    agent_behaviours = {}
    for agent in agents:
        agent_behaviours[agent.jid] = setup_agent(agent)

    logger.debug(f"Agent behaviours: {agent_behaviours}")

    return agent_behaviours
