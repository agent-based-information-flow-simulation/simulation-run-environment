"""
a tool to visualize connections inside the network

how to run:
in the main loop add the following code (after starting the agents,
instead of the loop with 'time.sleep' as it starts the blocking GUI loop):

    import math
    import matplotlib.pyplot as plt
    from matplotlib import animation

    fig = plt.figure()
    # matplotlib requires to use this '_' variable. don't ask why. it's python.
    _ = animation.FuncAnimation(
        fig,
        visualize_connections,
        fargs=(graph_creator.agents,),
        interval=math.sqrt(agents_count) * 1000,
    )

    # agents will start appearing while the GUI loop is running
    plt.show()

"""

import networkx as nx
import matplotlib.pyplot as plt
import hashlib
from .server import AGENT_TYPE_STYLE


def get_id(jid):
    return hashlib.md5(str(jid).encode()).hexdigest()


def visualize_connections(epoch, agents):
    print(f"Epoch: {epoch}")
    plt.clf()

    graph = nx.DiGraph()

    edges = []
    for agent in agents:
        graph.add_node(
            get_id(agent.jid),
            attr_dict={
                "type": agent.type,
                "followers": len(agent.adj_list),
            },
            pos=(agent.location),
        )

        for neighbour_jid in agent.adj_list:
            edges.append((get_id(agent.jid), get_id(neighbour_jid)))

    graph.add_edges_from(edges)

    # use 'AGENT_TYPE_STYLE' as it stores (as its keys)
    # all the agent types supported in visualization
    num_types = len(AGENT_TYPE_STYLE)
    type_to_color_map = {}
    for i, agent_type in enumerate(AGENT_TYPE_STYLE):
        type_to_color_map[agent_type] = i / num_types

    node_colors = [type_to_color_map.get(agent.type, 1.0) for agent in agents]

    pos_dict = nx.get_node_attributes(graph, "pos")
    positions = {}
    for node, position in zip(pos_dict.keys(), pos_dict.values()):
        positions[node] = position

    nx.draw_networkx_nodes(
        graph,
        positions,
        cmap=plt.get_cmap("jet"),
        node_color=node_colors,
        node_size=500,
        alpha=0.5,
    )

    nx.draw_networkx_edges(graph, positions, arrows=True, arrowsize=15, alpha=0.5)

    attr_dict = nx.get_node_attributes(graph, "attr_dict")
    labels = {}
    for node, attr_dict in zip(graph.nodes(), attr_dict.values()):
        labels[node] = {
            "id": node,
            "t": attr_dict["type"],
            "f": attr_dict["followers"],
        }

    # nx.draw_networkx_labels(
    #     graph, positions, font_size=12, font_weight="bold", labels=labels
    # )

    # legend = """
    # t - type
    # f - followers count
    # """
    # plt.text(0.02, 0.5, legend, fontsize=14, transform=plt.gcf().transFigure)
    plt.get_current_fig_manager().set_window_title("Fake news simulator")
    plt.title("Network graph")
