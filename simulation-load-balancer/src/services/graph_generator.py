from __future__ import annotations

from typing import Any, Dict, List

import httpx
from starlette import status

from src.exceptions import GraphGeneratorException
from src.services.base import BaseServiceWithoutRepository
from src.settings import graph_generator_settings


class GraphGeneratorService(BaseServiceWithoutRepository):
    async def generate(self, graph_code_lines: List[str]) -> List[Dict[str, Any]]:
        graph_generator_data = {"graph_code_lines": graph_code_lines}

        async with httpx.AsyncClient(
            base_url=graph_generator_settings.url, timeout=None
        ) as client:
            graph_generator_response = await client.post(
                "/python", json=graph_generator_data
            )

        graph_generator_response_body = graph_generator_response.json()

        if graph_generator_response.status_code != status.HTTP_200_OK:
            raise GraphGeneratorException(
                graph_generator_response.status_code, str(graph_generator_response_body)
            )

        return graph_generator_response_body["graph"]
