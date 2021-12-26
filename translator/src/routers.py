from __future__ import annotations

import httpx
from aasm import __version__, get_spade_code
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_201_CREATED

from src.models import AgentsAssemblyCode, CreatedSimulation
from src.settings import graph_generator_settings

router = APIRouter()


@router.post("/simulations", response_model=CreatedSimulation, status_code=201)
async def translate_aasm(agent_assembly_code: AgentsAssemblyCode):
    spade_code = get_spade_code(agent_assembly_code.code_lines)

    data = {
        "agent_code_lines": spade_code.agent_code_lines,
        "graph_code_lines": spade_code.graph_code_lines,
    }
    async with httpx.AsyncClient(base_url=graph_generator_settings.url) as client:
        response = await client.post("/graphs", json=data)

    if response.status_code == HTTP_201_CREATED:
        return {"simulation_id": response.json()["simulation_id"]}

    raise HTTPException(500, "Could not create a simulation.")
