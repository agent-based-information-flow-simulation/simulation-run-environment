from __future__ import annotations

from typing import Any, Dict

import httpx
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from src.exceptions import SimulationException
from src.models import CreateSimulation
from src.settings import backup_settings, instance_settings
from src.state import state

router = APIRouter()


@router.post("/simulations", status_code=201)
async def create_simulation(simulation_data: CreateSimulation):
    try:
        state.start_simulation_process(
            simulation_data.agent_code_lines, simulation_data.agent_data
        )
    except SimulationException as e:
        raise HTTPException(400, str(e))


@router.delete("/simulations")
async def delete_simulation():
    try:
        state.kill_simulation_process()
    except SimulationException as e:
        raise HTTPException(400, (e))


@router.post("/simulations/agent_data")
async def backup_agent_data(body: Dict[Any, Any]):
    agent_data = {"instance_id": instance_settings.id, "agent_data": body}
    async with httpx.AsyncClient() as client:
        await client.post(backup_settings.api_backup_url, json=agent_data)
