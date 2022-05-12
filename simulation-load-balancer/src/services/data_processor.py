from __future__ import annotations

from typing import Any, Dict, List

import httpx
from starlette import status

from src.exceptions import DataProcessorException
from src.models import StatusResponse
from src.services.base import BaseServiceWithoutRepository
from src.settings import data_processor_settings


class DataProcessorService(BaseServiceWithoutRepository):
    async def save_state(
        self, simulation_id: str, graph: List[Dict[str, Any]]
    ) -> StatusResponse:
        async with httpx.AsyncClient(
            base_url=data_processor_settings.url, timeout=None
        ) as client:
            response = await client.post(
                f"/simulations/{simulation_id}/backup", json=graph
            )
            if response.status_code != status.HTTP_200_OK:
                raise DataProcessorException(
                    response.status_code, "Couldn't save backup"
                )
            return StatusResponse(status_code=response.status_code, status="success")

    async def get_backup(self, simulation_id: str) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(
            base_url=data_processor_settings.url, timeout=None
        ) as client:
            response = await client.get(f"simulations/{simulation_id}/backup")
            if response.status_code != status.HTTP_200_OK:
                raise DataProcessorException(
                    response.status_code, "Couldn't load backup"
                )
            return response.content
