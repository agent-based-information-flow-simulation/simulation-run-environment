from __future__ import annotations

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.params import Depends
from fastapi.responses import ORJSONResponse

from src.dependencies import graph_runner_service
from src.models import PythonCode
from src.services import GraphRunnerService

router = APIRouter()


@router.post("/python")
async def generate_graph(
    python_code: PythonCode,
    graph_runner_service: GraphRunnerService = Depends(graph_runner_service),
):
    try:
        graph = graph_runner_service.run_algorithm(python_code.graph_code_lines)
    except Exception as e:
        raise HTTPException(500, f"Could not generate graph ({e}).")
    return ORJSONResponse(
        content={"graph": graph},
        status_code=200,
        headers={"Content-Type": "application/json"},
    )
