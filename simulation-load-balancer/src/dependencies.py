from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Type

from src.services.graph_generator import GraphGeneratorService
from src.services.translator import TranslatorService

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
