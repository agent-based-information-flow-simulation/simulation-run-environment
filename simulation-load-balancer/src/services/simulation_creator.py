from __future__ import annotations

from typing import Any, Dict, List
from aioredis import Redis

import httpx
from starlette import status

from src.exceptions import SimulationCreatorException
from src.services.base import BaseServiceWithoutRepository
from src.settings import simulation_load_balancer_settings
from src.models import InstanceData
from uuid import uuid4

import logging


def split_into_instances(graph: List[Dict[str, Any]], n: int) -> List[List[Dict[str, Any]]]:
     return [graph[i:i+n] for i in range(0, len(graph), n)]


class SimulationCreatorService(BaseServiceWithoutRepository):

    async def create(self, agent_code_lines: List[str], graph: List[Dict[str, Any]],
                     instances: List[InstanceData]) -> str:
        simulation_id = str(uuid4())[:10]
        instance_agents = split_into_instances(graph, len(instances))

        i = 0
        for instance, agents in zip(instances, instance_agents):
            simulation_data = {"simulation_id": simulation_id, "agent_code_lines": agent_code_lines,
                               "agent_data": agents}
            url = f"http://{str(instance['key'])}:8000"
            logging.warning(f"{url}")
            async with httpx.AsyncClient(base_url=url) as client:
                spade_instance_response = await client.post(
                    "/simulation", json=simulation_data,
                )
                spade_instance_response_body = spade_instance_response.json()
                if spade_instance_response.status_code != status.HTTP_200_OK:
                    raise SimulationCreatorException(
                        spade_instance_response.status_code, str(spade_instance_response_body)
                    )
        return simulation_id
