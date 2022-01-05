import asyncio
import logging
import time
from typing import Any, Dict, List

import aioxmpp
import spade
from spade.container import Container

from src.settings import backup_settings, communication_server_settings


# TLS is set to false
async def _async_register(agent):
    metadata = aioxmpp.make_security_layer(
        None, no_verify=not agent.verify_security
    )._replace(tls_required=False)
    query = aioxmpp.ibr.Query(agent.jid.localpart, agent.password)
    _, stream, features = await aioxmpp.node.connect_xmlstream(
        agent.jid, metadata, loop=agent.loop
    )
    await aioxmpp.ibr.register(stream, query)


# TLS is set to false
# register and connect client
async def _async_connect(agent):
    await agent._hook_plugin_before_connection()
    await _async_register(agent)
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
def _setup(agent):
    agent.setup()
    agent._alive.set()
    for behaviour in agent.behaviours:
        if not behaviour.is_running:
            behaviour.set_agent(agent)
            if issubclass(type(behaviour), spade.behaviour.FSMBehaviour):
                for _, state in behaviour.get_states().items():
                    state.set_agent(agent)
            behaviour.start()


def main(agent_code_lines: List[str], agent_data: List[Dict[str, Any]]):
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
            **agent_data_dict
        )
        agents.append(agent)

    for agent in agents:
        asyncio.run_coroutine_threadsafe(
            _async_connect(agent), loop=Container().loop
        ).result()

    for agent in agents:
        _setup(agent)

    while True:
        Container().reset()
        time.sleep(5)
