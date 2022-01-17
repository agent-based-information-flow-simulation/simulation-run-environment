from __future__ import annotations

from typing import List

from pydantic import BaseModel


class CreateSpadeSimulation(BaseModel):
    aasm_code_lines: List[str]


class CreatedSimulation(BaseModel):
    simulation_id: str
    info: str

class InstanceState(BaseModel):
    status: str
    simulation_id: str = None
    num_agents: int
    broken_agents: List[str]
    api_memory_usage_MiB: float
    simulation_memory_usage_MiB: float

class InstanceData(InstanceState):
    key: str
    simulation_id: str = None
    num_agents: int
    broken_agents: List[str]
    api_memory_usage_MiB: float
    simulation_memory_usage_MiB: float
