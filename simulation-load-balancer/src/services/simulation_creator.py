from __future__ import annotations

from typing import Any, Dict, List
from aioredis import Redis

import httpx
from starlette import status

from src.exceptions import SimulationCreatorException
from src.services.base import BaseServiceWithoutRepository
from src.settings import simulation_load_balancer_settings
from src.models import InstanceData, InstanceErrorData
from uuid import uuid4

import logging


def split_into_instances(graph: List[Dict[str, Any]], n: int) -> List[List[Dict[str, Any]]]:
    batch_size, rem = divmod(len(graph), n)
    batches = [graph[i * batch_size + min(i, rem):(i + 1) * batch_size + min(i + 1, rem)] for i in range(n)]
    return batches


# async def creation_task(simulation_id: str, agent_code_lines: List[str], agents: List[Dict[str, Any]], url: str) ->


class SimulationCreatorService(BaseServiceWithoutRepository):

    async def delete_simulation(self, instances: List[InstanceData]):
        for instance in instances:
            url = f"http://{str(instance['key'])}:8000"
            async with httpx.AsyncClient(base_url=url) as client:
                spade_instance_response = await client.delete(
                    "/simulation"
                )

    async def create(self, agent_code_lines: List[str], graph: List[Dict[str, Any]],
                     instances: List[InstanceData]) -> (str, List[InstanceErrorData]):
        simulation_id = str(uuid4())[:10]
        instance_agents = split_into_instances(graph, len(instances))

        error_instances = []

        for instance, agents in zip(instances, instance_agents):
            simulation_data = {"simulation_id": simulation_id, "agent_code_lines": agent_code_lines,
                               "agent_data": agents}
            url = f"http://{str(instance['key'])}:8000"
            try:
                async with httpx.AsyncClient(base_url=url) as client:
                    spade_instance_response = await client.post(
                        "/simulation", json=simulation_data,
                    )
                    spade_instance_response_body = spade_instance_response.json()
                    if spade_instance_response.status_code != status.HTTP_201_CREATED:
                        error_instances.append(
                            InstanceErrorData(key=instance['key'], status_code=str(spade_instance_response.status_code),
                                              info=f"{instance['key']}: {str(spade_instance_response_body)}")
                        )
            except httpx.TimeoutException as e:
                error_instances.append(
                    InstanceErrorData(key=instance['key'], status_code="408",
                                      info=f"Connection timed out {instance['key']}")
                )

        return simulation_id,
