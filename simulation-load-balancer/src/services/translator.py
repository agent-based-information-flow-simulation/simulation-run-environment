from __future__ import annotations

from typing import List, Tuple

import httpx
from starlette import status

from src.exceptions import TranslatorException
from src.services.base import BaseServiceWithoutRepository
from src.settings import translator_settings


class TranslatorService(BaseServiceWithoutRepository):
    async def translate(
        self, aasm_code_lines: List[str]
    ) -> Tuple[List[str], List[str]]:
        translator_data = {"code_lines": aasm_code_lines}

        async with httpx.AsyncClient(base_url=translator_settings.url) as client:
            translator_response = await client.post(
                "/python/spade", json=translator_data
            )

        translator_response_body = translator_response.json()

        if translator_response.status_code != status.HTTP_200_OK:
            raise TranslatorException(
                translator_response.status_code, str(translator_response_body)
            )

        return (
            translator_response_body["agent_code_lines"],
            translator_response_body["graph_code_lines"],
        )
