from __future__ import annotations

from typing import Any, Dict, List
from aioredis import Redis

import httpx
from starlette import status

from src.exceptions import DataProcessorException
from src.services.base import BaseServiceWithoutRepository
from src.settings import data_processor_settings
from src.models import StatusResponse
from uuid import uuid4

import logging


class DataProcessorService(BaseServiceWithoutRepository):
    async def save_state(self, simulation_id: str, graph: List[Dict[str, Any]]) -> StatusResponse:
        async with httpx.AsyncClient(base_url=data_processor_settings.url) as client:
            response = await client.post(f"/simulations/{simulation_id}/backup", json=graph)
            if response.status_code != status.HTTP_200_OK:
                raise DataProcessorException(
                    response.status_code, ""
                )
            return StatusResponse(status_code=response.status_code, status="success")
