from __future__ import annotations

import os

from pydantic import BaseSettings


class AppSettings(BaseSettings):
    client_cors_domain: str = os.environ.get("CLIENT_CORS_DOMAIN", "")
    enable_reload: bool = bool(os.environ.get("RELOAD", False))
    port: int = int(os.environ.get("PORT", 8000))


class GraphGeneratorSettings(BaseSettings):
    url: str = os.environ.get("GRAPH_GENERATOR_URL", "")


app_settings = AppSettings()
graph_generator_settings = GraphGeneratorSettings()
