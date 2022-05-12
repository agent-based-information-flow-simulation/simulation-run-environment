from __future__ import annotations

import logging
import os

from pydantic import BaseSettings


def configure_logging() -> None:
    logging.basicConfig(format="%(levelname)s:     [%(name)s] %(message)s")


class AppSettings(BaseSettings):
    enable_reload: bool = bool(os.environ.get("RELOAD", False))
    port: int = int(os.environ.get("PORT", 8000))


class RedisSettings(BaseSettings):
    redis_address: str = os.environ.get("REDIS_ADDRESS", "")
    redis_port: int = int(os.environ.get("REDIS_PORT", 6379))
    redis_password: str = os.environ.get("REDIS_PASSWORD", "")


class TranslatorSettings(BaseSettings):
    url: str = os.environ.get("TRANSLATOR_URL", "")


class GraphGeneratorSettings(BaseSettings):
    url: str = os.environ.get("GRAPH_GENERATOR_URL", "")


class SimulationLoadBalancerSettings(BaseSettings):
    max_per_instance: str = os.environ.get("MAX_AGENTS_PER_INSTANCE", "50")


class DataProcessorSettings(BaseSettings):
    url: str = os.environ.get("DATA_PROCESSOR_URL", "")


app_settings = AppSettings()
redis_settings = RedisSettings()
translator_settings = TranslatorSettings()
graph_generator_settings = GraphGeneratorSettings()
simulation_load_balancer_settings = SimulationLoadBalancerSettings()
data_processor_settings = DataProcessorSettings()
