from __future__ import annotations

from typing import AsyncGenerator, Callable, Type

from fastapi import Depends
from neo4j import AsyncSession, Neo4jDriver
from starlette.requests import Request

from src.db.repositories.base import BaseRepository
from src.services.backup import BackupService
from src.services.base import BaseService
from src.services.statistics import StatisticsService


def get_db_driver(request: Request) -> Neo4jDriver:
    return request.app.state.db_driver


async def get_session_from_db_pool(
    db_driver: Neo4jDriver = Depends(get_db_driver),
) -> AsyncGenerator[AsyncSession, None, None]:
    async with db_driver.session() as session:
        yield session


def get_repository(
    repository_type: Type[BaseRepository],
) -> Callable[[AsyncSession], BaseRepository]:
    def _get_repository(
        session: AsyncSession = Depends(get_session_from_db_pool),
    ) -> BaseRepository:
        return repository_type(session)

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


backup_service: Callable[[], BackupService] = get_service(BackupService)
statistics_service: Callable[[], StatisticsService] = get_service(StatisticsService)
