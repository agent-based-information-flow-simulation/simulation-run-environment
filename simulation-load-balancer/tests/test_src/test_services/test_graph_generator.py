from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.exceptions import GraphGeneratorException
from src.settings import graph_generator_settings

if TYPE_CHECKING:
    from pytest_httpx import HTTPXMock

    from src.services.graph_generator import GraphGeneratorService

pytestmark = pytest.mark.asyncio


async def test_after_providing_code_generate_returns_graph(
    graph_generator_service: GraphGeneratorService, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{graph_generator_settings.url}/python",
        method="POST",
        status_code=200,
        json={"graph": []},
    )

    code = []

    result = await graph_generator_service.generate(code)

    assert result == []


async def test_after_graph_generator_does_not_return_status_200_generate_raises_graph_generator_exception(
    graph_generator_service: GraphGeneratorService, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{graph_generator_settings.url}/python",
        method="POST",
        status_code=500,
        json={},
    )

    code = []

    with pytest.raises(GraphGeneratorException):
        await graph_generator_service.generate(code)
