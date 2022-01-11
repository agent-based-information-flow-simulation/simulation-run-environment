from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorDatabase


class BaseRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self._db = db

    @property
    def db(self) -> AsyncIOMotorDatabase:
        return self._db


class SimulationRepository(BaseRepository):
    async def insert_agent(self, sim_id: str, agent_data: Dict[str, Any]) -> None:
        collection = self.db.get_collection(sim_id)
        await collection.insert_one({"_id": agent_data["jid"], **agent_data})
        
    async def delete_all_agents(self, sim_id: str) -> None:
        collection = self.db.get_collection(sim_id)
        await collection.delete_many({})

    async def get_all_agents(self, sim_id: str) -> List[Dict[str, Any]]:
        collection = self.db.get_collection(sim_id)
        agents = []
        async for item in collection.find({}):
            agents.append(item)
        return agents
