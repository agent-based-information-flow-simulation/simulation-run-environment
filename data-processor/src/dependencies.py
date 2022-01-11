from __future__ import annotations

from typing import Callable, Type

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.db.repositories import BaseRepository
from src.services import AgentService, BaseService
from starlette.requests import Request


def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db_client["simulations"]


def get_repository(
    repository_type: Type[BaseRepository],
) -> Callable[[AsyncIOMotorDatabase], BaseRepository]:
    def _get_repository(
        db: AsyncIOMotorDatabase = Depends(get_db),
    ) -> BaseRepository:
        return repository_type(db)

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


agent_service: Callable[[], AgentService] = get_service(AgentService)
