import sys
import time
from pprint import pprint

import requests as r

PROXY_HOSTNAME_WITH_PORT = sys.argv[1]
URL = f"http://{PROXY_HOSTNAME_WITH_PORT}/v2"
GET_VERSION_URL = f"{URL}/services/haproxy/configuration/backends"
ENDPOINT_USER = sys.argv[2]
ENDPOINT_PASSWORD = sys.argv[3]
NUM_MAX_RETRIES = int(sys.argv[4])
IMAGE_HOSTNAME = sys.argv[5]
BACKEND_NAME = sys.argv[6]
BACKEND_PORT = int(sys.argv[7])


def register(backend_name, port):
    server_name = f"{backend_name}-{IMAGE_HOSTNAME}"
    add_server_url = (
        f"{URL}/services/haproxy/configuration/servers?backend={backend_name}&version="
    )
    version = r.get(GET_VERSION_URL, auth=(ENDPOINT_USER, ENDPOINT_PASSWORD)).json()[
        "_version"
    ]
    retries = 0
    while retries < NUM_MAX_RETRIES:
        response = r.post(
            f"{add_server_url}{version}",
            auth=(ENDPOINT_USER, ENDPOINT_PASSWORD),
            json={
                "name": server_name,
                "address": IMAGE_HOSTNAME,
                "port": port,
                "check": "enabled",
                "init-addr": "last,libc,none",
            },
        )
        if response.status_code == 202:
            print(
                f"Server {server_name} (port {port}) added to haproxy backend {backend_name}"
            )
            return
        elif (
            f"Server {server_name} already exists in backend"
            in response.json()["message"]
        ):
            print(
                f"Server {server_name} is already registered in haproxy backend {backend_name}"
            )
            return
        else:
            pprint(response.json())
            version += 1
            retries += 1
            time.sleep(1)
    print(f"Could not add server to haproxy backend {backend_name}")
    exit(1)


register(BACKEND_NAME, BACKEND_PORT)
