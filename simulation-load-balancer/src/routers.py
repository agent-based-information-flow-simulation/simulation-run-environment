from __future__ import annotations

from typing import Any, Dict, List

import httpx
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from starlette import status

from src.models import CreatedSimulation, CreateSpadeSimulation
from src.settings import graph_generator_settings, translator_settings

router = APIRouter()


@router.post("/simulations", response_model=CreatedSimulation, status_code=201)
async def create_simulation(simulation_data: CreateSpadeSimulation):
    translator_data = {
        "code_lines": simulation_data.aasm_code_lines,
    }
    async with httpx.AsyncClient(base_url=translator_settings.url) as client:
        translator_response = await client.post("/python/spade", json=translator_data)
    translator_response_body = translator_response.json()

    if translator_response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            500,
            f"Could not create a simulation (translator: [{translator_response.status_code} status] {translator_response_body}).",
        )

    graph_generator_data = {
        "agent_code_lines": translator_response_body["agent_code_lines"],
        "graph_code_lines": translator_response_body["graph_code_lines"],
    }
    async with httpx.AsyncClient(base_url=graph_generator_settings.url) as client:
        graph_generator_response = await client.post(
            "/python", json=graph_generator_data
        )
    graph_generator_response_body = graph_generator_response.json()

    if graph_generator_response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            500,
            f"Could not create a simulation (graph generator: [{graph_generator_response.status_code} status] {graph_generator_response_body}).",
        )

    agent_code_lines: List[str] = translator_response_body["agent_code_lines"]
    graph: List[Dict[str, Any]] = graph_generator_response_body["graph"]

    # start the simulation
    # ...

    return {"simulation_id": "test_123"}
