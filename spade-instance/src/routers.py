from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from src.models import CreateSimulation


router = APIRouter()


@router.post("/simulations", status_code=201)
async def create_simulation(simulation_data: CreateSimulation):
    ...
