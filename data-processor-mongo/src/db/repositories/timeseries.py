from __future__ import annotations

import numbers
from typing import TYPE_CHECKING

import orjson

from src.db.repositories.base import BaseRepository

if TYPE_CHECKING:
    from typing import Any, Dict, Generator

    from motor.motor_asyncio import AsyncIOMotorCursor
    from pymongo.results import DeleteResult


class DbCursorWrapper:
    def __init__(self, cursor: AsyncIOMotorCursor):
        self._cursor = cursor

    async def stream(self, chunk_size_bytes: int) -> Generator[bytes, None, None]:
        if chunk_size_bytes < 1:
            raise RuntimeError(
                "chunk_size_bytes must be greater than the size of an empty byte string"
            )
        if not isinstance(chunk_size_bytes, numbers.Integral):
            raise RuntimeError("chunk_size_bytes must be an integer")

        bytes_to_send = b"["
        is_separating_comma_required = False

        async for item in self._cursor:
            dumped = orjson.dumps(item)

            if is_separating_comma_required:
                dumped = b"," + dumped
            else:
                is_separating_comma_required = True

            dumped_idx = 0
            dumped_size = len(dumped)

            while dumped_idx < dumped_size:
                available_size = chunk_size_bytes - len(bytes_to_send)

                dumped_size_left = dumped_size - dumped_idx
                if available_size >= dumped_size_left:
                    bytes_to_send += dumped[dumped_idx:]
                    dumped_idx = dumped_size
                else:
                    bytes_to_send += dumped[dumped_idx : dumped_idx + available_size]
                    dumped_idx += available_size

                if len(bytes_to_send) == chunk_size_bytes:
                    yield bytes_to_send
                    bytes_to_send = b""

        if bytes_to_send and len(bytes_to_send) < chunk_size_bytes:
            yield bytes_to_send + b"]"
        elif bytes_to_send:
            yield bytes_to_send
            yield b"]"
        else:
            yield b"]"


class TimeseriesRepository(BaseRepository):
    collection_name = "agents"

    async def timeseries_exists(self, simulation_id: str) -> bool:
        result: Dict[str, Any] | None = await self.collection.find_one(
            {"metadata.simulation_id": simulation_id}, session=self.session
        )
        return result is not None

    async def get_timeseries(self, simulation_id: str) -> DbCursorWrapper:
        cursor: AsyncIOMotorCursor = self.collection.find(
            {"metadata.simulation_id": simulation_id},
            {"_id": False, "metadata": False, "timestamp": False},
            session=self.session,
        )
        return DbCursorWrapper(cursor)

    async def delete_timeseries(self, simulation_id: str) -> int:
        result: DeleteResult = await self.collection.delete_many(
            {"metadata.simulation_id": simulation_id}
        )
        return result.deleted_count
