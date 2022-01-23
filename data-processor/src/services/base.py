from __future__ import annotations

from typing import Type

from src.db.repositories.base import BaseRepository


class BaseService:
    repository_type: Type[BaseRepository] = BaseRepository

    def __init__(self, repository: BaseRepository) -> None:
        self._repository = repository

    @property
    def repository(self) -> repository_type:
        ...
