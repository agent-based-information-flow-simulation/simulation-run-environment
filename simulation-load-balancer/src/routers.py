from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from src.dependencies import graph_generator_service, translator_service
from src.exceptions import GraphGeneratorException, TranslatorException
from src.models import CreatedSimulation, CreateSpadeSimulation
from src.services.graph_generator import GraphGeneratorService
from src.services.translator import TranslatorService

router = APIRouter()


@router.post("/simulations", response_model=CreatedSimulation, status_code=201)
async def create_simulation(
    simulation_data: CreateSpadeSimulation,
    translator_service: TranslatorService = Depends(translator_service),
    graph_generator_service: GraphGeneratorService = Depends(graph_generator_service),
):
    try:
        agent_code_lines, graph_code_lines = await translator_service.translate(
            simulation_data.aasm_code_lines
        )
    except TranslatorException as e:
        raise HTTPException(500, f"Could not create a simulation (translator: {e}).")

    try:
        graph = await graph_generator_service.generate(graph_code_lines)
    except GraphGeneratorException as e:
        raise HTTPException(
            500, f"Could not create a simulation (graph generator: {e})."
        )

    # start the simulation
    # ...

    return {"simulation_id": "test_123"}
