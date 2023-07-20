from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from starlette import status

if TYPE_CHECKING:
    from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_after_sending_aasm_code_response_has_agent_code(
    client: AsyncClient,
) -> None:
    code = {
        "code_lines": [
            "agent test",
            "eagent",
        ],
        "module_lines": []
    }

    response = await client.post("/python/spade", json=code)

    assert "agent_code_lines" in response.json()

async def test_after_sending_aasm_code_response_has_module_code(
    client: AsyncClient,
) -> None:
    code = {
        "code_lines": [
            "agent test",
            "eagent",
        ],
        "module_lines": [
            [
                "!name test",
                "!targets",
                "spade",
            ],
        ]
    }

    response = await client.post("/python/spade", json=code)

    assert "module_code_lines" in response.json()

async def test_after_sending_aasm_code_response_has_graph_code(
    client: AsyncClient,
) -> None:
    code = {
        "code_lines": [
            "agent test",
            "eagent",
            "graph statistical",
            "defg test, 1, 0",
            "egraph",
        ],
        "module_lines": []
    }

    response = await client.post("/python/spade", json=code)

    assert "graph_code_lines" in response.json()


async def test_after_sending_aasm_code_response_has_200_status_code(
    client: AsyncClient,
) -> None:
    code = {
        "code_lines": [
            "agent test",
            "eagent",
            "graph statistical",
            "defg test, 1, 0",
            "egraph",
        ],
        "module_lines": []
    }

    response = await client.post("/python/spade", json=code)

    assert response.status_code == status.HTTP_200_OK
