from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from starlette import status

from src.dependencies import graph_generator_service, translator_service
from src.exceptions import GraphGeneratorException, TranslatorException

if TYPE_CHECKING:
    from fastapi import FastAPI
    from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_after_creating_simulaton_response_has_simulation_id(
    app: FastAPI, client: AsyncClient
) -> None:
    translator_service_mock = Mock()
    translate_future = asyncio.Future()
    translate_future.set_result(([], []))
    translator_service_mock.translate.return_value = translate_future
    app.dependency_overrides[translator_service] = lambda: translator_service_mock

    graph_generator_service_mock = Mock()
    generate_future = asyncio.Future()
    generate_future.set_result([])
    graph_generator_service_mock.generate.return_value = generate_future
    app.dependency_overrides[
        graph_generator_service
    ] = lambda: graph_generator_service_mock

    code = {"aasm_code_lines": []}

    response = await client.post("/simulations", json=code)

    assert "simulation_id" in response.json()


async def test_after_creating_simulaton_response_has_201_status_code(
    app: FastAPI, client: AsyncClient
) -> None:
    translator_service_mock = Mock()
    translate_future = asyncio.Future()
    translate_future.set_result(([], []))
    translator_service_mock.translate.return_value = translate_future
    app.dependency_overrides[translator_service] = lambda: translator_service_mock

    graph_generator_service_mock = Mock()
    generate_future = asyncio.Future()
    generate_future.set_result([])
    graph_generator_service_mock.generate.return_value = generate_future
    app.dependency_overrides[
        graph_generator_service
    ] = lambda: graph_generator_service_mock

    code = {"aasm_code_lines": []}

    response = await client.post("/simulations", json=code)

    assert response.status_code == status.HTTP_201_CREATED


async def test_after_simulation_was_not_created_due_to_translator_error_response_has_500_status_code(
    app: FastAPI, client: AsyncClient
) -> None:
    translator_service_mock = Mock()
    translate_future = asyncio.Future()
    translate_future.set_exception(TranslatorException(0, ""))
    translator_service_mock.translate.side_effect = translate_future
    app.dependency_overrides[translator_service] = lambda: translator_service_mock

    code = {"aasm_code_lines": []}

    response = await client.post("/simulations", json=code)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


async def test_after_simulation_was_not_created_due_to_translator_error_response_has_details(
    app: FastAPI, client: AsyncClient
) -> None:
    translator_service_mock = Mock()
    translate_future = asyncio.Future()
    translate_future.set_exception(TranslatorException(0, ""))
    translator_service_mock.translate.side_effect = translate_future
    app.dependency_overrides[translator_service] = lambda: translator_service_mock

    code = {"aasm_code_lines": []}

    response = await client.post("/simulations", json=code)

    assert "detail" in response.json()


async def test_after_simulation_was_not_created_due_to_graph_generator_error_response_has_500_status_code(
    app: FastAPI, client: AsyncClient
) -> None:
    translator_service_mock = Mock()
    translate_future = asyncio.Future()
    translate_future.set_result(([], []))
    translator_service_mock.translate.return_value = translate_future
    app.dependency_overrides[translator_service] = lambda: translator_service_mock

    graph_generator_service_mock = Mock()
    generate_future = asyncio.Future()
    generate_future.set_exception(GraphGeneratorException(0, ""))
    graph_generator_service_mock.generate.side_effect = generate_future
    app.dependency_overrides[
        graph_generator_service
    ] = lambda: graph_generator_service_mock

    code = {"aasm_code_lines": []}

    response = await client.post("/simulations", json=code)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


async def test_after_simulation_was_not_created_due_to_graph_generator_error_response_has_details(
    app: FastAPI, client: AsyncClient
) -> None:
    translator_service_mock = Mock()
    translate_future = asyncio.Future()
    translate_future.set_result(([], []))
    translator_service_mock.translate.return_value = translate_future
    app.dependency_overrides[translator_service] = lambda: translator_service_mock

    graph_generator_service_mock = Mock()
    generate_future = asyncio.Future()
    generate_future.set_exception(GraphGeneratorException(0, ""))
    graph_generator_service_mock.generate.side_effect = generate_future
    app.dependency_overrides[
        graph_generator_service
    ] = lambda: graph_generator_service_mock

    code = {"aasm_code_lines": []}

    response = await client.post("/simulations", json=code)

    assert "detail" in response.json()
