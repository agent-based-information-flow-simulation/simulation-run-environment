from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorCollection


class BaseRepository:
    collection_name: str = ""

    def __init__(
        self, session: AsyncIOMotorClientSession, collection: AsyncIOMotorCollection
    ):
        self._session = session
        self._collection = collection

    @property
    def session(self) -> AsyncIOMotorClientSession:
        return self._session

    @property
    def collection(self) -> AsyncIOMotorCollection:
        return self._collection
