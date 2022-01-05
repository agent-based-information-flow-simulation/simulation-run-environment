from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Type

from src.services import GraphRunnerService

if TYPE_CHECKING:  # pragma: no cover
    from src.services import BaseService


def _get_service(service_type: Type[BaseService]) -> Callable[[], BaseService]:
    def __get_service() -> BaseService:
        return service_type()

    return __get_service


graph_runner_service: Callable[[], GraphRunnerService] = _get_service(
    GraphRunnerService
)
