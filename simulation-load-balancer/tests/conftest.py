from __future__ import annotations

from typing import TYPE_CHECKING, List

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from src.app import get_app
from src.services.graph_generator import GraphGeneratorService
from src.services.translator import TranslatorService
from src.settings import app_settings, graph_generator_settings, translator_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


graph_generator_settings.url = "http://fake-graph-generator"
translator_settings.url = "http://fake-translator"


@pytest.fixture
async def app() -> FastAPI:
    app = get_app()
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    port = app_settings.port
    base_url = f"http://simulation-load-balancer:{port}"
    async with AsyncClient(app=app, base_url=base_url) as client:
        yield client


@pytest.fixture
def non_mocked_hosts() -> List[str]:
    return ["simulation-load-balancer"]


@pytest.fixture
def graph_generator_service() -> GraphGeneratorService:
    yield GraphGeneratorService()


@pytest.fixture
def translator_service() -> TranslatorService:
    yield TranslatorService()
