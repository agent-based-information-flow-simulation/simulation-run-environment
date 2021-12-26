from __future__ import annotations

from fastapi import APIRouter

from src.models import CreatedSimulation, CreateSpadeSimulationData

router = APIRouter()


@router.post("/simulations", response_model=CreatedSimulation, status_code=201)
async def create_simulation(simulation_data: CreateSpadeSimulationData):
    return {"simulation_id": "test_123"}
