import datetime
import getopt
import json
import os
import sys
import threading
import webbrowser

import dash
import flask
import pandas as pd
import plotly.graph_objects as go
# import dash_html_components as html
# import dash_core_components as dcc
from dash import dcc, html
from dash.dependencies import Input, Output

# server
HOST = "127.0.0.1"
PORT = 8050
SERVER_MESSAGE_QUEUE = []
SERVER_MESSAGES = {}
SERVER_AGENTS = {}
DEFAULT_IS_VERBOSE = False

# gui
REFRESH_INTERVAL_MS = 10000
MIN_REFRESH_INTERVAL_MS = 1000
MAX_REFRESH_INTERVAL_MS = 60 * 1000
STEP_REFRESH_INTERVAL_MS = 100
EPOCH = 0

# neighbours
MARKER_MAX_SIZE = 20
MARKER_MIN_SIZE = 5
DEFAULT_MARKER_SIZE = 10

# topics
MAX_SUSCEPTIBILITY = 100
MIN_SUSCEPTIBILITY = 0
MAX_SATURATION = 100
MIN_SATURATION = 25
TOPIC_HUE = {0: 120, 1: 240, 2: 30, 3: 180, 4: 300}
UNKNOWN_TOPIC_HUE = 0

# agent types
AGENT_TYPE_STYLE = {"common": "circle", "bot": "square"}
UKNOWN_AGENT_TYPE_STYLE = "x"

# message types
MESSAGE_TYPE_STYLE = {"fakenews": "rgb(255,0,0)", "debunk": "rgb(0,255,0)"}
MESSAGE_TYPE_SHIFT = {
    "fakenews": {"x": 0.05, "y": 0.05},
    "debunk": {"x": -0.05, "y": -0.05},
}


def parse_cli_args():
    usage_str = (
        f"Usage: {sys.argv[0]} [-h] [-v (sets verbosity, default={DEFAULT_IS_VERBOSE})]"
    )

    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hv")
    except getopt.GetoptError:
        print(usage_str)
        sys.exit(2)

    is_verbose = DEFAULT_IS_VERBOSE

    for opt, _ in opts:
        if opt == "-h":
            print(usage_str)
            sys.exit(0)
        elif opt == "-v":
            is_verbose = not DEFAULT_IS_VERBOSE

    return is_verbose


def main():
    IS_VERBOSE = parse_cli_args()
    threading.Timer(1, open_new_tab).start()

    server = flask.Flask(__name__)

    @server.route("/messages", methods=["POST"])
    def post_messages():
        msgs = json.loads(flask.request.data)

        for msg in msgs:
            SERVER_MESSAGE_QUEUE.append(msg)

            full_msg = json.loads(msg["full_msg"])
            msg_parent_id = full_msg["parent_id"]
            if msg_parent_id in SERVER_MESSAGES:
                SERVER_MESSAGES[msg_parent_id]["counter"] += 1
            else:
                SERVER_MESSAGES[msg_parent_id] = full_msg
                SERVER_MESSAGES[msg_parent_id]["counter"] = 1

            SERVER_MESSAGES[msg_parent_id]["last_update"] = datetime.datetime.now()

            if IS_VERBOSE:
                print(
                    f"received msg. current queue: {len(SERVER_MESSAGE_QUEUE)} msgs, msg: {msg}"
                )

        return flask.Response("", 201)

    @server.route("/agents", methods=["POST"])
    def post_agents():
        agent_dict = json.loads(flask.request.data)
        agent_jid, agent_data = list(agent_dict.items())[0]

        try:
            SERVER_AGENTS[agent_jid] = agent_data
        except KeyError as e:
            print(f"Couldn't add agent {agent_dict}, missing key: {e}")
            return flask.Response("", 418)

        if IS_VERBOSE:
            print(
                f"received agent. total: {len(SERVER_AGENTS)} agents, agent: {agent_dict}"
            )

        return flask.Response("", 201)

    external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

    app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)
    app.title = "Fakenews Simulator"
    app.layout = html.Div(
        html.Div(
            [
                html.H4("Fakenews simulator - network graph"),
                html.Div(id="epoch-text"),
                html.Div(
                    id="refresh-interval-text",
                    children=f"Refresh interval: {REFRESH_INTERVAL_MS / 1000}s",
                ),
                html.Div(children="Change the refresh interval:"),
                dcc.Slider(
                    id="refresh-interval-slider",
                    min=MIN_REFRESH_INTERVAL_MS,
                    max=MAX_REFRESH_INTERVAL_MS,
                    step=STEP_REFRESH_INTERVAL_MS,
                    value=REFRESH_INTERVAL_MS,
                ),
                html.Div(id="state-text"),
                html.Button("stop", id="stop-button"),
                html.Button("resume", id="resume-button"),
                html.Button("clean", id="clean-button"),
                dcc.Graph(id="graph", style={"height": "100vh"}),
                dcc.Graph(id="table", style={"height": "100vh"}),
                dcc.Interval(
                    id="interval-component",
                    interval=REFRESH_INTERVAL_MS,
                    n_intervals=0,
                ),
            ]
        )
    )

    # note to self: if you ever see a python library that says "no js required" just don't use it
    @app.callback(
        [
            Output("interval-component", "interval"),
            Output("refresh-interval-text", "children"),
            Output("state-text", "children"),
        ],
        [
            Input("stop-button", "n_clicks"),
            Input("resume-button", "n_clicks"),
            Input("refresh-interval-slider", "value"),
        ],
    )
    def modify_interval(stop, resume, slider_value_ms):
        global REFRESH_INTERVAL_MS
        context = dash.callback_context

        if (
            not context.triggered
            or context.triggered[0]["prop_id"].split(".")[0] == "resume-button"
        ):
            refresh_interval_text = f"Refresh interval: {REFRESH_INTERVAL_MS / 1000}s"
            state_text = "State: running"
            return [REFRESH_INTERVAL_MS, refresh_interval_text, state_text]

        elif context.triggered[0]["prop_id"].split(".")[0] == "stop-button":
            # it's impossible to stop the interval completely so I set it to a big value
            refresh_interval_text = f"Refresh interval: {REFRESH_INTERVAL_MS / 1000}s"
            state_text = "State: stopped"
            return [1000 * 60 * 60 * 24 * 365, refresh_interval_text, state_text]

        else:
            REFRESH_INTERVAL_MS = slider_value_ms
            refresh_interval_text = f"Refresh interval: {REFRESH_INTERVAL_MS / 1000}s"
            state_text = "State: running"
            return [REFRESH_INTERVAL_MS, refresh_interval_text, state_text]

    @app.callback(
        Output("epoch-text", "children"),
        [Input("interval-component", "n_intervals"), Input("clean-button", "n_clicks")],
    )
    def update_epoch(n_intervals, n_clicks):
        global SERVER_MESSAGE_QUEUE
        global SERVER_AGENTS
        global EPOCH
        global SERVER_MESSAGES

        context = dash.callback_context

        if context.triggered[0]["prop_id"].split(".")[0] == "clean-button":
            SERVER_MESSAGE_QUEUE = []
            SERVER_AGENTS = {}
            EPOCH = 1
            SERVER_MESSAGES = {}
        else:
            EPOCH += 1

        return html.Span(f"Epoch: {EPOCH}")

    def update_graph():
        # it's cleared after reading all pending messages
        global SERVER_MESSAGE_QUEUE

        print("updating graph...")
        start_time = datetime.datetime.now()

        fig = go.Figure(
            layout=go.Layout(
                titlefont_size=16,
                showlegend=False,
                hovermode="closest",
                annotations=[
                    dict(
                        text="<a href='https://github.com/agent-systems-org/FakeNewsSimulator/'>Source</a>",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.005,
                        y=-0.002,
                    )
                ],
                margin=dict(b=20, l=5, r=5, t=20),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            ),
        )

        edges = {}
        for msg_type, color in MESSAGE_TYPE_STYLE.items():
            edges[msg_type] = {
                "edge_x": [],
                "edge_y": [],
                "style": dict(width=0.5, color=color),
            }

        # prevents race conditions
        message_queue_copy = list(SERVER_MESSAGE_QUEUE)
        SERVER_MESSAGE_QUEUE = []

        for msg_data in message_queue_copy:
            try:
                x0, y0 = SERVER_AGENTS[msg_data["from_jid"]]["location"]
                x1, y1 = SERVER_AGENTS[msg_data["to_jid"]]["location"]
                msg_type = msg_data["type"]
                x_shift = MESSAGE_TYPE_SHIFT[msg_type]["x"]
                y_shift = MESSAGE_TYPE_SHIFT[msg_type]["y"]
                edges[msg_type]["edge_x"].append(x0 + x_shift)
                edges[msg_type]["edge_x"].append(x1 + x_shift)
                edges[msg_type]["edge_x"].append(None)
                edges[msg_type]["edge_y"].append(y0 - y_shift)
                edges[msg_type]["edge_y"].append(y1 - y_shift)
                edges[msg_type]["edge_y"].append(None)

            except KeyError as e:
                print(f"Data on server is incomplete for {msg_data}, missing key: {e}")

        for edge_type_dict in edges.values():
            edge_trace = go.Scatter(
                x=edge_type_dict["edge_x"],
                y=edge_type_dict["edge_y"],
                line=edge_type_dict["style"],
                hoverinfo="none",
                mode="lines",
            )
            fig.add_trace(edge_trace)

        if SERVER_AGENTS:
            # prevents race conditions
            agents_data_copy = list(SERVER_AGENTS.values())
        else:
            agents_data_copy = []

        max_neighbours = -sys.maxsize
        min_neighbours = sys.maxsize
        for agent_data in agents_data_copy:
            try:
                if agent_data["neighbours_count"] < min_neighbours:
                    min_neighbours = agent_data["neighbours_count"]

                elif agent_data["neighbours_count"] > max_neighbours:
                    max_neighbours = agent_data["neighbours_count"]

            except KeyError as e:
                print(
                    f"Data on server is incomplete for {agent_data}, missing key: {e}"
                )

        if max_neighbours != min_neighbours:
            a_marker_coeff = (MARKER_MAX_SIZE - MARKER_MIN_SIZE) / (
                max_neighbours - min_neighbours
            )
            b_marker_coeff = MARKER_MAX_SIZE - max_neighbours * a_marker_coeff
            get_marker_size = lambda n_count: n_count * a_marker_coeff + b_marker_coeff
        else:
            get_marker_size = lambda n_count: DEFAULT_MARKER_SIZE

        a_sus_coeff = (MAX_SATURATION - MIN_SATURATION) / (
            MAX_SUSCEPTIBILITY - MIN_SUSCEPTIBILITY
        )
        b_sus_coeff = MAX_SATURATION - MAX_SUSCEPTIBILITY * a_sus_coeff
        get_saturation = lambda sus: sus * a_sus_coeff + b_sus_coeff

        for agent_data in agents_data_copy:
            try:
                x, y = agent_data["location"]

                agent_type = agent_data["type"]
                marker_symbol = AGENT_TYPE_STYLE.get(
                    agent_type, UKNOWN_AGENT_TYPE_STYLE
                )

                susceptible_topic = agent_data["susceptible_topic"]
                susceptibility = agent_data["susceptibility"]
                hue = TOPIC_HUE.get(susceptible_topic, UNKNOWN_TOPIC_HUE)
                color = f"hsv({hue},{get_saturation(susceptibility)}%,100%)"

                neighbours_count = agent_data["neighbours_count"]

                node_trace = go.Scatter(
                    x=[x],
                    y=[y],
                    marker_symbol=marker_symbol,
                    marker=dict(size=get_marker_size(neighbours_count), color=color),
                    mode="markers",
                    hoverinfo="text",
                    text=f"followers: {neighbours_count}, susceptible topic: {susceptible_topic}, susceptibility: {susceptibility}, type: {agent_data['type']}",
                )
                fig.add_trace(node_trace)

            except KeyError as e:
                print(
                    f"Data on server is incomplete for {agent_data}, missing key: {e}"
                )

        elapsed_time = datetime.datetime.now() - start_time
        num_displayed_agents = len(agents_data_copy)
        num_displayed_msgs = len(message_queue_copy)
        print(
            f"done updating graph: {num_displayed_agents} agents, {num_displayed_msgs} msgs ({int(elapsed_time.total_seconds() * 1000)} ms)."
        )

        return fig

    def update_table():
        if len(SERVER_MESSAGES) > 0:
            server_messages_copy = dict(SERVER_MESSAGES)
            df = pd.DataFrame.from_dict(server_messages_copy, orient="index")

            df["parent_id"] = df["parent_id"].apply(lambda i: str(i)[:10] + "...")
            df = df.sort_values(by="last_update", ascending=False)

            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(
                            values=["parent_id", "counter", "last_update"],
                            fill_color="paleturquoise",
                            align="left",
                        ),
                        cells=dict(
                            values=[df.parent_id, df.counter, df.last_update],
                            fill_color="lavender",
                            align="left",
                        ),
                    )
                ]
            )

            return fig

        return go.Figure()

    @app.callback(
        [Output("graph", "figure"), Output("table", "figure")],
        Input("interval-component", "n_intervals"),
    )
    def update_figures(n_intervals):
        return [update_graph(), update_table()]

    app.run_server(debug=True, host=HOST, port=PORT)


def open_new_tab():
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new_tab(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    main()
