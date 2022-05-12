from __future__ import annotations

from typing import TYPE_CHECKING

from src.db.repositories.timeseries import DbCursorWrapper, TimeseriesRepository
from src.exceptions import TimeseriesDoesNotExistException
from src.services.base import BaseService

if TYPE_CHECKING:
    from typing import List


class TimeseriesService(BaseService):
    repository_type = TimeseriesRepository

    @property
    def repository(self) -> repository_type:
        return self._repository

    async def get_timeseries(self, simulation_id: str) -> DbCursorWrapper:
        if not await self.repository.timeseries_exists(simulation_id):
            raise TimeseriesDoesNotExistException(simulation_id)
        return await self.repository.get_timeseries(simulation_id)

    async def delete_timeseries(self, simulation_id) -> int:
        if not await self.repository.timeseries_exists(simulation_id):
            raise TimeseriesDoesNotExistException(simulation_id)
        return await self.repository.delete_timeseries(simulation_id)

    async def get_all_timeseries_ids(self) -> List[str]:
        return await self.repository.get_all_timeseries_ids()
