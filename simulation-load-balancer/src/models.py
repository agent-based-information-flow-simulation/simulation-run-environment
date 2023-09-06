from __future__ import annotations

from typing import List

from pydantic import BaseModel


class CreateSpadeSimulation(BaseModel):
    aasm_code_lines: List[str]
    module_code_lines: List[List[str]]
    seed: int


class CreatedSimulation(BaseModel):
    simulation_id: str
    info: str
    status: str


class SimulationData(CreatedSimulation):
    simulation_id: str
    info: str | None = None
    status: str


class InstanceState(BaseModel):
    status: str
    simulation_id: str | None = None
    num_agents: int
    broken_agents: List[str]
    api_memory_usage_MiB: float
    simulation_memory_usage_MiB: float


class InstanceData(InstanceState):
    key: str


class InstanceErrorData(BaseModel):
    key: str
    status_code: str
    info: str


class SimulationLoadBalancerState(BaseModel):
    instances: List[InstanceData]
    simulations: List[SimulationData]
    environment: str


class StatusResponse(BaseModel):
    status: str
    status_code: str
