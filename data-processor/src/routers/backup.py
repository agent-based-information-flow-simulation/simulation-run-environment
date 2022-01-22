from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import ORJSONResponse

from src.dependencies import backup_service
from src.exceptions import (
    SimulationBackupAlreadyExistsException,
    SimulationBackupDoesNotExistException,
)
from src.models import CreateAgent
from src.services.backup import BackupService

router = APIRouter(prefix="/simulations", default_response_class=ORJSONResponse)


@router.post("/{simulation_id}/backup")
async def create_backup(
    simulation_id: str,
    agent_data: List[CreateAgent],
    backup_service: BackupService = Depends(backup_service),
):
    try:
        await backup_service.create_backup(simulation_id, agent_data)
    except SimulationBackupAlreadyExistsException as e:
        raise HTTPException(400, str(e))


@router.get("/{simulation_id}/backup")
async def get_backup(
    simulation_id: str,
    backup_service: BackupService = Depends(backup_service),
):
    try:
        return await backup_service.get_backup(simulation_id)
    except SimulationBackupDoesNotExistException as e:
        raise HTTPException(400, str(e))


@router.delete("/{simulation_id}/backup")
async def delete_backup(
    simulation_id: str,
    backup_service: BackupService = Depends(backup_service),
):
    try:
        await backup_service.delete_backup(simulation_id)
    except SimulationBackupDoesNotExistException as e:
        raise HTTPException(400, str(e))
