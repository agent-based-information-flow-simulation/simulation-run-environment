from __future__ import annotations

from typing import List

from pydantic import BaseModel


class AgentsAssemblyCode(BaseModel):
    code_lines: List[str]


class CreatedSimulation(BaseModel):
    simulation_id: str
