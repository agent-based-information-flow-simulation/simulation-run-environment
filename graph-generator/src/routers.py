from __future__ import annotations

import httpx
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.params import Depends
from starlette.status import HTTP_201_CREATED

from src.dependencies import graph_runner_service
from src.models import CreatedSimulation, PythonCode
from src.services import GraphRunnerService
from src.settings import simulation_load_balancer_settings

router = APIRouter()


@router.post("/graphs", response_model=CreatedSimulation, status_code=201)
async def generate_graph(
    python_code: PythonCode,
    graph_runner_service: GraphRunnerService = Depends(graph_runner_service),
):
    graph = graph_runner_service.run_algorithm(python_code.graph_code_lines)
    data = {"agent_code_lines": python_code.agent_code_lines, "graph": graph}
    async with httpx.AsyncClient(
        base_url=simulation_load_balancer_settings.url
    ) as client:
        response = await client.post("/simulations", json=data)

    if response.status_code == HTTP_201_CREATED:
        return {"simulation_id": response.json()["simulation_id"]}

    raise HTTPException(500, "Could not create a simulation.")
