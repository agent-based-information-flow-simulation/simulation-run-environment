from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from starlette import status

from src.settings import graph_generator_settings, translator_settings

if TYPE_CHECKING:
    from httpx import AsyncClient
    from pytest_httpx import HTTPXMock

pytestmark = pytest.mark.asyncio


async def test_after_creating_simulaton_response_has_simulation_id(
    client: AsyncClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{translator_settings.url}/python/spade",
        method="POST",
        status_code=200,
        json={"agent_code_lines": [], "graph_code_lines": []},
    )
    httpx_mock.add_response(
        url=f"{graph_generator_settings.url}/python",
        method="POST",
        status_code=200,
        json={"graph": []},
    )
    code = {
        "aasm_code_lines": [
            "agent test",
            "eagent",
            "graph statistical",
            "defg test, 1, 0",
            "egraph",
        ]
    }

    response = await client.post("/simulations", json=code)

    assert "simulation_id" in response.json()


async def test_after_creating_simulaton_response_has_201_status_code(
    client: AsyncClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{translator_settings.url}/python/spade",
        method="POST",
        status_code=200,
        json={"agent_code_lines": [], "graph_code_lines": []},
    )
    httpx_mock.add_response(
        url=f"{graph_generator_settings.url}/python",
        method="POST",
        status_code=200,
        json={"graph": []},
    )
    code = {
        "aasm_code_lines": [
            "agent test",
            "eagent",
            "graph statistical",
            "defg test, 1, 0",
            "egraph",
        ]
    }

    response = await client.post("/simulations", json=code)

    assert response.status_code == status.HTTP_201_CREATED


async def test_after_simulation_was_not_created_due_to_translator_error_response_has_500_status_code(
    client: AsyncClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{translator_settings.url}/python/spade",
        method="POST",
        status_code=500,
        json={},
    )
    code = {
        "aasm_code_lines": [
            "agent test",
            "eagent",
            "graph statistical",
            "defg test, 1, 0",
            "egraph",
        ]
    }

    response = await client.post("/simulations", json=code)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


async def test_after_simulation_was_not_created_due_to_translator_error_response_has_details(
    client: AsyncClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{translator_settings.url}/python/spade",
        method="POST",
        status_code=500,
        json={},
    )
    code = {
        "aasm_code_lines": [
            "agent test",
            "eagent",
            "graph statistical",
            "defg test, 1, 0",
            "egraph",
        ]
    }

    response = await client.post("/simulations", json=code)

    assert "detail" in response.json()


async def test_after_simulation_was_not_created_due_to_graph_generator_error_response_has_500_status_code(
    client: AsyncClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{translator_settings.url}/python/spade",
        method="POST",
        status_code=200,
        json={"agent_code_lines": [], "graph_code_lines": []},
    )
    httpx_mock.add_response(
        url=f"{graph_generator_settings.url}/python",
        method="POST",
        status_code=500,
        json={},
    )
    code = {
        "aasm_code_lines": [
            "agent test",
            "eagent",
            "graph statistical",
            "defg test, 1, 0",
            "egraph",
        ]
    }

    response = await client.post("/simulations", json=code)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


async def test_after_simulation_was_not_created_due_to_graph_generator_error_response_has_details(
    client: AsyncClient, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{translator_settings.url}/python/spade",
        method="POST",
        status_code=200,
        json={"agent_code_lines": [], "graph_code_lines": []},
    )
    httpx_mock.add_response(
        url=f"{graph_generator_settings.url}/python",
        method="POST",
        status_code=500,
        json={},
    )
    code = {
        "aasm_code_lines": [
            "agent test",
            "eagent",
            "graph statistical",
            "defg test, 1, 0",
            "egraph",
        ]
    }

    response = await client.post("/simulations", json=code)

    assert "detail" in response.json()
