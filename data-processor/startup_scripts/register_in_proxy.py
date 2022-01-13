import sys
import time
from pprint import pprint

import requests as r

IMAGE_HOSTNAME = sys.argv[1]
URL = "http://data-processor-proxy:5555/v2"
GET_VERSION_URL = f"{URL}/services/haproxy/configuration/backends"
ENDPOINT_USER = "admin"
ENDPOINT_PASSWORD = "admin"
NUM_MAX_RETRIES = 100


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
            print(f"Server {server_name} added to haproxy")
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
    print("Could not add server to haproxy backend {backend_name}")
    exit(1)


register("data_processor", 8000)
