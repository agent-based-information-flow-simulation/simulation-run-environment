from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.exceptions import TranslatorException
from src.settings import translator_settings

if TYPE_CHECKING:
    from pytest_httpx import HTTPXMock

    from src.services.translator import TranslatorService

pytestmark = pytest.mark.asyncio


async def test_after_providing_valid_aasm_code_translate_returns_tuple_with_code(
    translator_service: TranslatorService, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{translator_settings.url}/python/spade",
        method="POST",
        status_code=200,
        json={"agent_code_lines": [], "graph_code_lines": []},
    )

    aasm_code_lines = []

    result = await translator_service.translate(aasm_code_lines)

    assert result == ([], [])


async def test_after_translator_does_not_return_status_200_translate_raises_translator_exception(
    translator_service: TranslatorService, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=f"{translator_settings.url}/python/spade",
        method="POST",
        status_code=500,
        json={},
    )

    aasm_code_lines = []

    with pytest.raises(TranslatorException):
        await translator_service.translate(aasm_code_lines)
