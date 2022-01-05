import json
import threading

import agents.utils
import requests

from .server import HOST, PORT

URL = f"http://{HOST}:{PORT}"


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, agents.utils.Message):
            return obj.toJSON()
        return json.JSONEncoder.default(self, obj)


# TODO fix imports and use this class in json.loads() inside server.py in post_messages()
class CustomJsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    # pylint: disable=E0202
    def object_hook(self, dct):
        if "full_msg" in dct:
            return agents.utils.Message.fromJSON(dct["full_msg"])
        return dct


def send_post(url, json_data):
    try:
        requests.post(url, json_data)
    except Exception:
        print(f"Couldn't post data to {url}")


def post_messages(msgs):
    """
    non-blocking

    msgs is a list of messages

    a message: {
        "from_jid": JID
        "to_jid": JID
        "type": string
        "full_msg": agents.utils.Message
    }

    supported message types:
        check visualization/server.py
    """

    msg_dicts = []
    for msg in msgs:
        msg_dicts.append(
            {
                "from_jid": str(msg["from_jid"]),
                "to_jid": str(msg["to_jid"]),
                "type": msg["type"],
                "full_msg": msg["full_msg"],
            }
        )

    data = json.dumps(msg_dicts, cls=CustomJsonEncoder)
    threading.Thread(target=send_post, args=(URL + "/messages", data)).start()


def post_agent(agent):
    """
    non-blocking

    agent must have following properties:
        location: tuple, i.e. (x, y)
        neighbours_count: number
        susceptibility: number
        susceptible_topic: int
        type: string

    supported susceptibility range:
        check visualization/server.py

    supported agent types:
        check visualization/server.py

    supported susceptible topics:
        check visualization/server.py
    """

    agent_data = {
        str(agent.jid): {
            "location": agent.location,
            "neighbours_count": len(agent.adj_list),
            "susceptibility": agent.susceptibility,
            "susceptible_topic": agent.susceptible_topic,
            "type": agent.type,
        }
    }
    data = json.dumps(agent_data)
    threading.Thread(target=send_post, args=(URL + "/agents", data)).start()
