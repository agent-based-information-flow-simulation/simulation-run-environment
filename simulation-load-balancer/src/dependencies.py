from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Type
from starlette.requests import Request
from aioredis import Redis

from src.services.graph_generator import GraphGeneratorService
from src.services.translator import TranslatorService
from src.services.simulation_creator import SimulationCreatorService
from src.services.data_processor import DataProcessorService

if TYPE_CHECKING:  # pragma: no cover
    from src.services import BaseServiceWithoutRepository


def _get_service_without_repository(
        service_type: Type[BaseServiceWithoutRepository],
) -> Callable[[], BaseServiceWithoutRepository]:
    def __get_service_without_repository() -> BaseServiceWithoutRepository:
        return service_type()

    return __get_service_without_repository


translator_service: Callable[[], TranslatorService] = _get_service_without_repository(
    TranslatorService
)
graph_generator_service: Callable[
    [], GraphGeneratorService
] = _get_service_without_repository(GraphGeneratorService)
simulation_creator_service: Callable[
    [], SimulationCreatorService
] = _get_service_without_repository(SimulationCreatorService)
data_processor_service: Callable[
    [], DataProcessorService
] = _get_service_without_repository(DataProcessorService)


def create_get_redis() -> Callable[[Request], Redis]:
    def get_redis(request: Request):
        return request.app.state.redis

    return get_redis


redis: Callable[[Request], Redis] = create_get_redis()