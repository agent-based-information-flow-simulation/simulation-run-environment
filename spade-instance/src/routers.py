from __future__ import annotations

import logging
import os

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from src.dependencies import state
from src.exceptions import SimulationException
from src.models import CreateSimulation, DeletedSimulation
from src.state import State

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_ROUTERS", "INFO"))

router = APIRouter()


@router.get("/healthcheck", status_code=200)
async def healthcheck():
    return {"response": "success"}


@router.post("/simulation", status_code=201)
async def create_simulation(
    simulation_data: CreateSimulation, state: State = Depends(state)
):
    logger.debug(
        f"Creating simulation {simulation_data.simulation_id}, state: {await state.get_state()}"
    )
    try:
        await state.start_simulation_process(
            simulation_data.simulation_id,
            simulation_data.agent_code_lines,
            simulation_data.agent_data,
        )
    except SimulationException as e:
        raise HTTPException(400, str(e))


@router.delete("/simulation", response_model=DeletedSimulation, status_code=200)
async def delete_simulation(state: State = Depends(state)):
    logger.debug(f"Deleting simulation, state: {await state.get_state()}")
    _, simulation_id, _, _ = await state.get_state()
    try:
        await state.kill_simulation_process()
        return DeletedSimulation(simulation_id=simulation_id)
    except SimulationException as e:
        raise HTTPException(400, str(e))
