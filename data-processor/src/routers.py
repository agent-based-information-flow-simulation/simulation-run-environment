from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import ORJSONResponse

from src.dependencies import backup_service
from src.exceptions import SimulationBackupAlreadyExistsException
from src.models import CreateAgent
from src.services.backup import BackupService

router = APIRouter()


@router.post("/simulations/{simulation_id}/backup")
async def create_backup(
    simulation_id: str,
    agent_data: List[CreateAgent],
    backup_service: BackupService = Depends(backup_service),
):
    try:
        await backup_service.create_backup(simulation_id, agent_data)
    except SimulationBackupAlreadyExistsException as e:
        raise HTTPException(400, str(e))


@router.get("/simulations/{simulation_id}/backup")
async def get_backup(
    simulation_id: str,
    backup_service: BackupService = Depends(backup_service),
):
    backup = await backup_service.get_backup(simulation_id)
    return ORJSONResponse(
        headers={"Content-Type": "application/json"},
        content=backup,
    )


@router.delete("/simulations/{simulation_id}/backup")
async def delete_backup(
    simulation_id: str,
    backup_service: BackupService = Depends(backup_service),
):
    await backup_service.delete_backup(simulation_id)


@router.get("/simulations/{simulation_id}/statistics/{agent_type}")
async def get_agent_type_simple_property(
    simulation_id: str,
    agent_type: str,
    property: str,
    backup_service: BackupService = Depends(backup_service),
):
    properties = await backup_service.get_agent_type_properties(
        simulation_id, agent_type
    )
    return ORJSONResponse(
        headers={"Content-Type": "application/json"},
        content=properties,
    )
