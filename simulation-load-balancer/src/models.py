from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class CreateSpadeSimulationData(BaseModel):
    agent_code_lines: List[str]
    graph: List[Dict[str, Any]]


class CreatedSimulation(BaseModel):
    simulation_id: str
