from __future__ import annotations

from typing import Any, Dict, List, Type

from src.db.repositories import BaseRepository, SimulationRepository


class BaseService:
    repository_type: Type[BaseRepository] = BaseRepository

    def __init__(self, repository: BaseRepository) -> None:
        self._repository = repository

    @property
    def repository(self) -> BaseRepository:
        return self._repository


class BackupService(BaseService):
    repository_type = SimulationRepository


class AgentService(BaseService):
    repository_type = SimulationRepository

    async def insert_agent(self, sim_id: str, agent_data: Dict[str, Any]) -> None:
        await self.repository.insert_agent(sim_id, agent_data)
        
    async def delete_all_agents(self, sim_id: str) -> None:
        await self.repository.delete_all_agents(sim_id)

    async def get_all_agents(self, sim_id: str) -> List[Dict[str, Any]]:
        return await self.repository.get_all_agents(sim_id)
