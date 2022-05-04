from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorClientSession,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from starlette.requests import Request

from src.db.repositories.base import BaseRepository
from src.exceptions import CollectionDoesNotExistException
from src.services.base import BaseService
from src.services.timeseries import TimeseriesService

if TYPE_CHECKING:
    from typing import Any, AsyncGenerator, Callable, Coroutine, Type


def get_db_client(request: Request) -> AsyncIOMotorClient:
    return request.app.state.db_client


def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db


async def get_session_from_db_pool(
    db_client: AsyncIOMotorClient = Depends(get_db_client),
) -> AsyncGenerator[AsyncIOMotorClientSession, None, None]:
    async with await db_client.start_session() as session:
        yield session


def get_collection(
    collection_name: str,
) -> Callable[[AsyncIOMotorDatabase], Coroutine[Any, Any, AsyncIOMotorCollection]]:
    async def _get_collection(
        db: AsyncIOMotorDatabase = Depends(get_db),
    ) -> AsyncIOMotorCollection:
        if collection_name not in await db.list_collection_names():
            raise CollectionDoesNotExistException(collection_name)
        return db[collection_name]

    return _get_collection


def get_repository(
    repository_type: Type[BaseRepository],
) -> Callable[[AsyncIOMotorClientSession], BaseRepository]:
    def _get_repository(
        session: AsyncIOMotorClientSession = Depends(get_session_from_db_pool),
        collection: AsyncIOMotorCollection = Depends(
            get_collection(repository_type.collection_name)
        ),
    ) -> BaseRepository:
        return repository_type(session, collection)

    return _get_repository


def get_service(
    service_type: Type[BaseService],
) -> Callable[[BaseRepository], BaseService]:
    def _get_service(
        repository: BaseRepository = Depends(
            get_repository(service_type.repository_type)
        ),
    ) -> BaseService:
        return service_type(repository)

    return _get_service


timeseries_service: Callable[[], TimeseriesService] = get_service(TimeseriesService)
