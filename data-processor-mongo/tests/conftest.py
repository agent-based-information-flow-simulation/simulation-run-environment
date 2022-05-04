from __future__ import annotations

from typing import TYPE_CHECKING, List

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from src.app import get_app
from src.settings import app_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


@pytest.fixture
async def app() -> FastAPI:
    app = get_app(unit_tests=True)
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    port = app_settings.port
    base_url = f"http://data-processor-mongo:{port}"
    async with AsyncClient(app=app, base_url=base_url) as client:
        yield client


@pytest.fixture
def non_mocked_hosts() -> List[str]:
    return ["data-processor-mongo"]
