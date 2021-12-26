from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from starlette import status

from src.dependencies import graph_runner_service
from src.settings import simulation_load_balancer_settings

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx import AsyncClient
    from pytest_httpx import HTTPXMock

pytestmark = pytest.mark.asyncio


async def test_after_creating_simulaton_response_has_simulation_id(
    app: FastAPI, client: AsyncClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{simulation_load_balancer_settings.url}/simulations",
        method="POST",
        status_code=201,
        json={"simulation_id": "abc123"},
    )
    graph_structure = []
    graph_runner_service_mock = Mock()
    graph_runner_service_mock.run_algorithm.return_value = graph_structure
    app.dependency_overrides[graph_runner_service] = lambda: graph_runner_service_mock
    code = {"agent_code_lines": [], "graph_code_lines": []}

    response = await client.post("/graphs", json=code)

    assert response.json() == {"simulation_id": "abc123"}


async def test_after_creating_simulaton_response_has_201_status_code(
    app: FastAPI, client: AsyncClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{simulation_load_balancer_settings.url}/simulations",
        method="POST",
        status_code=201,
        json={"simulation_id": "abc123"},
    )
    graph_structure = []
    graph_runner_service_mock = Mock()
    graph_runner_service_mock.run_algorithm.return_value = graph_structure
    app.dependency_overrides[graph_runner_service] = lambda: graph_runner_service_mock
    code = {"agent_code_lines": [], "graph_code_lines": []}

    response = await client.post("/graphs", json=code)

    assert response.status_code == status.HTTP_201_CREATED


async def test_after_simulation_was_not_created_response_has_500_status_code(
    app: FastAPI, client: AsyncClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{simulation_load_balancer_settings.url}/simulations",
        method="POST",
        status_code=500,
    )
    graph_structure = []
    graph_runner_service_mock = Mock()
    graph_runner_service_mock.run_algorithm.return_value = graph_structure
    app.dependency_overrides[graph_runner_service] = lambda: graph_runner_service_mock
    code = {"agent_code_lines": [], "graph_code_lines": []}

    response = await client.post("/graphs", json=code)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


async def test_after_simulation_was_not_created_response_has_details(
    app: FastAPI, client: AsyncClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{simulation_load_balancer_settings.url}/simulations",
        method="POST",
        status_code=500,
    )
    graph_structure = []
    graph_runner_service_mock = Mock()
    graph_runner_service_mock.run_algorithm.return_value = graph_structure
    app.dependency_overrides[graph_runner_service] = lambda: graph_runner_service_mock
    code = {"agent_code_lines": [], "graph_code_lines": []}

    response = await client.post("/graphs", json=code)

    assert "detail" in response.json()
