from asyncio import futures
import concurrent
import time
import sys
import getopt
import math
from spade.container import Container
from spade import quit_spade
import matplotlib.pyplot as plt
from matplotlib import animation
import visualization
from agents import GraphCreator
import asyncio

DEFAULT_NUM_AGENTS = 80
DEFAULT_IS_CONNECTIONS_VISUALIZATION_ON = False


def parse_cli_args():
    usage_str = f"Usage: {sys.argv[0]} [-h] [-n <num_of_agents> (default={DEFAULT_NUM_AGENTS})] [-v (toggle visualization of connections, default={DEFAULT_IS_CONNECTIONS_VISUALIZATION_ON})]"

    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hvn:d:")
    except getopt.GetoptError:
        print(usage_str)
        sys.exit(2)

    num_agents = DEFAULT_NUM_AGENTS
    is_connections_visualization_on = DEFAULT_IS_CONNECTIONS_VISUALIZATION_ON
    domain = "0"

    for opt, arg in opts:
        if opt == "-h":
            print(usage_str)
            sys.exit(0)
        elif opt == "-n":
            num_agents = int(arg)
        elif opt == "-v":
            is_connections_visualization_on = (
                not DEFAULT_IS_CONNECTIONS_VISUALIZATION_ON
            )
        elif opt == "-d":
            domain = arg

    return num_agents, is_connections_visualization_on, domain

import aioxmpp
import logging
from spade.presence import PresenceManager
from aioxmpp.dispatcher import SimpleMessageDispatcher
from spade.behaviour import FSMBehaviour
import aioxmpp.ibr as ibr


# TLS is set to false
async def _async_register(agent):
    metadata = aioxmpp.make_security_layer(None, no_verify=not agent.verify_security)._replace(tls_required=False)
    query = ibr.Query(agent.jid.localpart, agent.password)
    _, stream, features = await aioxmpp.node.connect_xmlstream(
        agent.jid, metadata, loop=agent.loop
    )
    await ibr.register(stream, query)

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
    agent.message_dispatcher = agent.client.summon(SimpleMessageDispatcher)
    agent.presence = PresenceManager(agent)
    await agent._async_connect()
    agent.message_dispatcher.register_callback(
        aioxmpp.MessageType.CHAT, None, agent._message_received,
    )
    await agent._hook_plugin_after_connection()

# separate function to setup the agents after they are connected
def _setup(agent):
    agent.setup()
    agent._alive.set()
    for behaviour in agent.behaviours:
        if not behaviour.is_running:
            behaviour.set_agent(agent)
            if issubclass(type(behaviour), FSMBehaviour):
                for _, state in behaviour.get_states().items():
                    state.set_agent(agent)
            behaviour.start()


def main(num_agents, is_connections_visualization_on, domain):
    logger = logging.getLogger(aioxmpp.protocol.__name__)
    logger.setLevel(logging.DEBUG)
    logger.debug("test message")
    
    # num_agents, is_connections_visualization_on, domain = parse_cli_args()

    base = domain + "_fake_news"
    domain = "@agents-sim.xyz/0"
    password = "asdasdsdgghtr434bdsdg"
    
    print(f"Running simulation: {base}")

    graph_creator = GraphCreator(base, domain, password, num_agents)
    print(f"Creating network with {num_agents} agents")

    # graph_creator.start().result()
    asyncio.run_coroutine_threadsafe(_async_connect(graph_creator), loop=Container().loop).result()
    _setup(graph_creator)

    agents = graph_creator.agents

    # with concurrent.futures.ThreadPoolExecutor() as e:
    #     e.submit([agent.start() for agent in agents])
    
    num_connected_agents = 0
    num_concurrent_connections = 1
    for start_agents in zip(*[iter(agents)] * num_concurrent_connections):
        print(f"===== CONNECTING: {num_concurrent_connections} agents =====")
        futures = [asyncio.run_coroutine_threadsafe(_async_connect(agent), loop=Container().loop) for agent in start_agents]
        for future in futures:
            future.result()
        num_connected_agents += num_concurrent_connections
        print(f"Connected agents {num_connected_agents}")

    print("Done connecting :)")
    print("sleeping 10s... zzzzzz")
    time.sleep(10)
    
    for agent in agents:
        # print(f"===== SETUP: {agent.jid} =====")
        _setup(agent)
        
    print("Done with the setup :)")
    print("Let the battle begin")
    
    
    # for agent in agents:
    #     print(f"===== REGISTERING: {agent.jid} =====")
    #     asyncio.run_coroutine_threadsafe(agent._async_register(), loop=Container().loop).result()
        
    # for agent in agents:
    #     print(f"===== STARTING: {agent.jid} =====")
    #     agent.start(auto_register=False).result()

    if is_connections_visualization_on:
        fig = plt.figure()

        _ = animation.FuncAnimation(
            fig,
            visualization.visualize_connections,
            fargs=(agents,),
            interval=math.sqrt(len(agents)) * 1000,
        )

        plt.show()

    else:
        while True:
            Container().reset()
            try:
                time.sleep(5)
            except KeyboardInterrupt:
                break

    for agent in agents:
        agent.stop()

    quit_spade()


if __name__ == "__main__":
    num_agents, is_connections_visualization_on, domain = parse_cli_args()
    main(num_agents, is_connections_visualization_on, domain)
