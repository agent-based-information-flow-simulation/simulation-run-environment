from __future__ import annotations

import logging
from typing import Any, Dict, List

import httpx
from starlette import status

from src.models import InstanceData, InstanceErrorData
from src.services.base import BaseServiceWithoutRepository


def split_into_instances(
    graph: List[Dict[str, Any]], n: int
) -> List[List[Dict[str, Any]]]:
    batch_size, rem = divmod(len(graph), n)
    batches = [
        graph[i * batch_size + min(i, rem) : (i + 1) * batch_size + min(i + 1, rem)]
        for i in range(n)
    ]
    return batches


class SimulationCreatorService(BaseServiceWithoutRepository):
    async def delete_simulation_instances(
        self, instances: List[InstanceData]
    ) -> List[InstanceErrorData]:
        error_instances = []
        for instance in instances:
            url = f"http://{str(instance['key'])}:8000"
            try:
                async with httpx.AsyncClient(base_url=url, timeout=None) as client:
                    spade_instance_response = await client.delete("/simulation")
                    if spade_instance_response.status_code == status.HTTP_200_OK:
                        logging.info(f"Deleted instance {str(instance['key'])}")
                    else:
                        error_instances.append(
                            InstanceErrorData(
                                key=instance["key"],
                                status_code=str(spade_instance_response.status_code),
                                info=f"DeletionError: {instance['key']}",
                            )
                        )
            except Exception:
                error_instances.append(
                    InstanceErrorData(
                        key=instance["key"],
                        status_code="418",
                        info=f"DeletionError: {instance['key']}",
                    )
                )
        return error_instances

    async def check_health(
        self, instances: List[InstanceErrorData]
    ) -> List[InstanceErrorData]:
        bad_instances = []
        for instance in instances:
            url = f"http://{str(instance.key)}:8000"
            try:
                async with httpx.AsyncClient(base_url=url, timeout=None) as client:
                    spade_instance_response = await client.get("/healthcheck")
                    if spade_instance_response.status_code != status.HTTP_200_OK:
                        bad_instances.append(
                            InstanceErrorData(
                                key=instance.key,
                                status_code=spade_instance_response.status_code,
                                info=f"{instance.key}: Unexpected",
                            )
                        )
            except httpx.TimeoutException as e:
                bad_instances.append(
                    InstanceErrorData(
                        key=instance.key,
                        status_code=status.HTTP_408_REQUEST_TIMEOUT,
                        info=f"{instance.key}: Timeout",
                    )
                )
            except httpx.ConnectError as e:
                bad_instances.append(
                    InstanceErrorData(
                        key=instance.key,
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        info=f"{instance.key}: Unavailable",
                    )
                )
        return bad_instances

    async def create(
        self,
        agent_code_lines: List[str],
        graph: List[Dict[str, Any]],
        instances: List[InstanceData],
        simulation_id: str,
    ) -> List[InstanceErrorData]:
        instance_agents = split_into_instances(graph, len(instances))

        error_instances = []

        for instance, agents in zip(instances, instance_agents):
            simulation_data = {
                "simulation_id": simulation_id,
                "agent_code_lines": agent_code_lines,
                "agent_data": agents,
            }
            url = f"http://{str(instance['key'])}:8000"
            try:
                print(type(agents))
                async with httpx.AsyncClient(base_url=url, timeout=None) as client:
                    spade_instance_response = await client.post(
                        "/simulation",
                        json=simulation_data,
                    )
                    spade_instance_response_body = spade_instance_response.json()
                    if spade_instance_response.status_code != status.HTTP_201_CREATED:
                        error_instances.append(
                            InstanceErrorData(
                                key=instance["key"],
                                status_code=str(spade_instance_response.status_code),
                                info=f"{instance['key']}: {str(spade_instance_response_body)}",
                            )
                        )
            except Exception as e:
                print(e)
                error_instances.append(
                    InstanceErrorData(
                        key=instance["key"],
                        status_code="418",
                        info=f"Creation Error: {instance['key']}",
                    )
                )

        return error_instances
