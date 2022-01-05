from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from src.app import get_app
from src.services import GraphRunnerService
from src.settings import app_settings, communication_server_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


communication_server_settings.domain = "domain.test"


@pytest.fixture
async def app() -> FastAPI:
    app = get_app()
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    port = app_settings.port
    base_url = f"http://graph-generator:{port}"
    async with AsyncClient(app=app, base_url=base_url) as client:
        yield client


@pytest.fixture
def graph_runner_service() -> GraphRunnerService:
    yield GraphRunnerService()
