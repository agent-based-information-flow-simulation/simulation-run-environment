from __future__ import annotations

from typing import TYPE_CHECKING

from src.db.repositories.base import BaseRepository

if TYPE_CHECKING:
    from typing import Any, Dict, List

    from motor.motor_asyncio import AsyncIOMotorCursor
    from pymongo.results import DeleteResult


class TimeseriesRepository(BaseRepository):
    collection_name = "agents"

    async def timeseries_exists(self, simulation_id: str) -> bool:
        result: Dict[str, Any] | None = await self.collection.find_one(
            {"metadata.simulation_id": simulation_id}, session=self.session
        )
        return result is not None

    async def get_timeseries(self, simulation_id: str) -> List[Dict[str, Any]]:
        cursor: AsyncIOMotorCursor = self.collection.find(
            {"metadata.simulation_id": simulation_id},
            {"_id": False, "metadata": False, "timestamp": False},
            session=self.session,
        )
        return [item["agent"] async for item in cursor]

    async def delete_timeseries(self, simulation_id: str) -> int:
        result: DeleteResult = await self.collection.delete_many(
            {"metadata.simulation_id": simulation_id}
        )
        return result.deleted_count
