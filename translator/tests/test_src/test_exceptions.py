from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from starlette import status

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_after_sending_invalid_aasm_code_response_has_translator_details(
    client: AsyncClient,
) -> None:
    code = {
        "code_lines": ["eagent"],
        "module_lines": []
        }

    response = await client.post("/python/spade", json=code)

    assert "translator_version" in response.json()
    assert "place" in response.json()
    assert "reason" in response.json()
    assert "suggestion" in response.json()


async def test_after_sending_invalid_aasm_code_response_has_400_status_code(
    client: AsyncClient,
) -> None:
    code = {
        "code_lines": ["eagent"],
        "module_lines": []
        }

    response = await client.post("/python/spade", json=code)

    assert status.HTTP_400_BAD_REQUEST == response.status_code

async def test_after_sending_invalid_module_code_has_details(
    client: AsyncClient,
) -> None:
    code = {
        "code_lines": ["eagent"],
        "module_lines": [
            [
                "!name test",
                "!targets spade",
            ],
        ]
        }

    response = await client.post("/python/spade", json=code)

    assert "translator_version" in response.json()
    assert "place" in response.json()
    assert "reason" in response.json()
    assert "suggestion" in response.json()
