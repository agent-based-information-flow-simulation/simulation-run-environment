from __future__ import annotations

from typing import List

from pydantic import BaseModel


class CreateSpadeSimulation(BaseModel):
    aasm_code_lines: List[str]


class CreatedSimulation(BaseModel):
    simulation_id: str
