from __future__ import annotations

from typing import Any, Dict

from src.db.repositories.timeseries import TimeseriesRepository
from src.exceptions import TimeseriesDoesNotExistException
from src.services.base import BaseService


class TimeseriesService(BaseService):
    repository_type = TimeseriesRepository

    @property
    def repository(self) -> repository_type:
        return self._repository

    async def get_timeseries(self, simulation_id: str) -> Dict[str, Any]:
        if not await self.repository.timeseries_exists(simulation_id):
            raise TimeseriesDoesNotExistException(simulation_id)
        return await self.repository.get_timeseries(simulation_id)

    async def delete_timeseries(self, simulation_id) -> Dict[str, int]:
        if not await self.repository.timeseries_exists(simulation_id):
            raise TimeseriesDoesNotExistException(simulation_id)
        num_deleted = await self.repository.delete_timeseries(simulation_id)
        return {"deleted": num_deleted}
