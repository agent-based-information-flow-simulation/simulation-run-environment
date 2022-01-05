from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from starlette import status

from src.dependencies import graph_runner_service

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_after_sending_graph_code_response_has_graph_json(
    app: FastAPI, client: AsyncClient
) -> None:
    graph_runner_service_mock = Mock()
    graph_structure = []
    graph_runner_service_mock.run_algorithm.return_value = graph_structure
    app.dependency_overrides[graph_runner_service] = lambda: graph_runner_service_mock
    code = {"graph_code_lines": []}

    response = await client.post("/python", json=code)

    assert "graph" in response.json()
    assert graph_structure == response.json()["graph"]


async def test_after_creating_simulaton_response_has_200_status_code(
    app: FastAPI, client: AsyncClient
) -> None:
    graph_runner_service_mock = Mock()
    graph_structure = []
    graph_runner_service_mock.run_algorithm.return_value = graph_structure
    app.dependency_overrides[graph_runner_service] = lambda: graph_runner_service_mock
    code = {"graph_code_lines": []}

    response = await client.post("/python", json=code)

    assert response.status_code == status.HTTP_200_OK


async def test_after_graph_runner_service_fails_response_has_500_status_code(
    app: FastAPI, client: AsyncClient
) -> None:
    graph_runner_service_mock = Mock()
    graph_runner_service_mock.run_algorithm.side_effect = Exception()
    app.dependency_overrides[graph_runner_service] = lambda: graph_runner_service_mock
    code = {"graph_code_lines": []}

    response = await client.post("/python", json=code)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


async def test_after_graph_runner_service_fails_response_has_details(
    app: FastAPI, client: AsyncClient
) -> None:
    graph_runner_service_mock = Mock()
    graph_runner_service_mock.run_algorithm.side_effect = Exception()
    app.dependency_overrides[graph_runner_service] = lambda: graph_runner_service_mock
    code = {"graph_code_lines": []}

    response = await client.post("/python", json=code)

    assert "detail" in response.json()
