from __future__ import annotations

import os

from pydantic import BaseSettings


class AppSettings(BaseSettings):
    enable_reload: bool = bool(os.environ.get("RELOAD", False))
    port: int = int(os.environ.get("PORT", 8000))


class SimulationLoadBalancerSettings(BaseSettings):
    url: str = os.environ.get("SIMULATION_LOAD_BALANCER_URL", "")


class CommunicationServerSettings(BaseSettings):
    domain: str = os.environ.get("COMMUNICATION_SERVER_DOMAIN", "")


app_settings = AppSettings()
simulation_load_balancer_settings = SimulationLoadBalancerSettings()
communication_server_settings = CommunicationServerSettings()
