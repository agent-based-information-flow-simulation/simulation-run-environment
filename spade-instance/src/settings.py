from __future__ import annotations

import logging
import os

from pydantic import BaseSettings


def configure_logging() -> None:
    logging.basicConfig(format="%(levelname)s:\t  [%(name)s] %(message)s")
    logging.getLogger("uvicorn.access").setLevel(
        level=os.environ.get("LOG_LEVEL_UVICORN_ACCESS", "WARNING")
    )


class AppSettings(BaseSettings):
    enable_reload: bool = bool(os.environ.get("RELOAD", False))
    port: int = int(os.environ.get("PORT", 8000))


class BackupSettings(BaseSettings):
    agent_backup_url: str = os.environ.get("AGENT_BACKUP_URL", "")
    api_backup_url: str = os.environ.get("API_BACKUP_URL", "")
    period: int = int(os.environ.get("AGENT_BACKUP_PERIOD", 15))
    delay: int = int(os.environ.get("AGENT_BACKUP_DELAY", 5))


class CommunicationServerSettings(BaseSettings):
    password: str = os.environ.get("COMMUNICATION_SERVER_PASSWORD", "")


class InstanceSettings(BaseSettings):
    id: str = os.environ.get("HOSTNAME")
    status_url: str = os.environ.get("INSTANCE_STATUS_URL", "")
    process_health_check_period: int = int(
        os.environ.get("SIMULATION_PROCESS_HEALTH_CHECK_PERIOD", 5)
    )


class SimulationSettings(BaseSettings):
    registration_retry_after: int = int(
        os.environ.get("AGENT_REGISTRATION_RETRY_AFTER", 5)
    )
    registration_max_concurrency: int = int(
        os.environ.get("AGENT_REGISTRATION_MAX_CONCURRENCY", 5)
    )


class SimulationLoadBalancerSettings(BaseSettings):
    url: str = os.environ.get("SIMULATION_LOAD_BALANCER_URL", "")
    announcement_period: int = int(
        os.environ.get("SIMULATION_LOAD_BALANCER_ANNOUNCEMENT_PERIOD", 10)
    )


app_settings = AppSettings()
backup_settings = BackupSettings()
communication_server_settings = CommunicationServerSettings()
instance_settings = InstanceSettings()
simulation_settings = SimulationSettings()
simulation_load_balancer_settings = SimulationLoadBalancerSettings()
