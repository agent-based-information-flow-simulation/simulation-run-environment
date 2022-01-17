from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import ORJSONResponse

from src.dependencies import simulation_service
from src.exceptions import SimulationBackupAlreadyExistsException
from src.models import CreateAgent
from src.services import SimulationService

router = APIRouter()


@router.post("/simulations/{simulation_id}/backup")
async def create_backup(
    simulation_id: str,
    agent_data: List[CreateAgent],
    simulation_service: SimulationService = Depends(simulation_service),
):
    try:
        await simulation_service.create_backup(simulation_id, agent_data)
    except SimulationBackupAlreadyExistsException as e:
        raise HTTPException(400, str(e))


@router.get("/simulations/{simulation_id}/backup")
async def get_backup(
    simulation_id: str,
    simulation_service: SimulationService = Depends(simulation_service),
):
    backup = await simulation_service.get_backup(simulation_id)
    return ORJSONResponse(
        headers={"Content-Type": "application/json"},
        content=backup,
    )


@router.delete("/simulations/{simulation_id}/backup")
async def delete_backup(
    simulation_id: str,
    simulation_service: SimulationService = Depends(simulation_service),
):
    await simulation_service.delete_backup(simulation_id)
