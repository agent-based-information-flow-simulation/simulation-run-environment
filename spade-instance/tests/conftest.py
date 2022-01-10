from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List
from unittest.mock import Mock

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient

from src.app import get_app
from src.settings import (
    app_settings,
    backup_settings,
    simulation_load_balancer_settings,
    simulation_settings,
)
from src.state import State

if TYPE_CHECKING:
    from fastapi import FastAPI


simulation_load_balancer_settings.url = "http://fake-simulation-load-balancer"
backup_settings.agent_backup_url = "http://fake-agent-backup"
backup_settings.api_backup_url = "http://fake-api-backup"
simulation_settings.status_url = "http://fake-instance-status"


def check_called(function: Callable[[Any], Any]) -> Mock:
    return Mock(side_effect=function)


@pytest.fixture
async def app() -> FastAPI:
    app = get_app(unit_tests=True)
    async with LifespanManager(app):
        yield app


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    port = app_settings.port
    base_url = f"http://spade-instance:{port}"
    async with AsyncClient(app=app, base_url=base_url) as client:
        yield client


@pytest.fixture
def state() -> State:
    return State()


@pytest.fixture
def non_mocked_hosts() -> List[str]:
    return ["spade-instance"]
