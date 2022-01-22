from __future__ import annotations

import logging
import math
import os
from collections import Counter
from typing import Any, List

import numpy as np

from src.db.repositories.statistics import StatisticsRepository
from src.exceptions import (
    AgentTypeDoesNotExistException,
    InconsistentListDataTypesException,
    InvalidAgentTypeStatisticsRequestException,
    SimulationBackupDoesNotExistException,
)
from src.models import Statistics
from src.services.base import BaseService

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_SERVICES_STATISTICS", "INFO"))


class StatisticsService(BaseService):
    repository_type = StatisticsRepository

    @property
    def repository(self) -> repository_type:
        return self._repository

    def _get_numerical_statistics(self, data: List[float]) -> Statistics:
        # Sturge's rule
        num_bins = round(1 + 3.322 * math.log(len(data)))
        histogram, bin_edges = np.histogram(data, bins=num_bins)

        if len(bin_edges) == 2:
            labels = [f"[{bin_edges[0]} - {bin_edges[1]}]"]
        else:
            labels = []
            for i in range(len(bin_edges) - 2):
                labels.append(f"[{bin_edges[i]} - {bin_edges[i + 1]})")
            labels.append(f"[{bin_edges[-2]} - {bin_edges[-1]}]")

        return Statistics(data=list(histogram), labels=labels)

    def _get_categorical_statistics(self, data: List[str]) -> Statistics:
        counter = Counter(data)
        return Statistics(labels=list(counter.keys()), data=list(counter.values()))

    async def _get_agent_type_property(
        self, simulation_id: str, agent_type: str, property_: str
    ) -> Statistics:
        agent_type_property_record = await self.repository.get_agent_type_property(
            simulation_id, agent_type, property_
        )

        if not agent_type_property_record or not agent_type_property_record["property"]:
            return Statistics(labels=[], data=[])

        data: List[Any] = agent_type_property_record["property"]

        if all(isinstance(item, (int, float)) for item in data):
            return self._get_numerical_statistics(data)
        elif all(isinstance(item, str) for item in data):
            return self._get_categorical_statistics(data)
        else:
            raise InconsistentListDataTypesException(
                simulation_id, agent_type, property_, data
            )

    async def get_agent_type_statistics(
        self,
        simulation_id: str,
        agent_type: str,
        property_: str,
        message_list: str,
        message_type: str,
        connection_list: str,
    ) -> Statistics:
        if not await self.repository.simulation_exists(simulation_id):
            raise SimulationBackupDoesNotExistException(simulation_id)

        if not await self.repository.agent_type_exists(simulation_id, agent_type):
            raise AgentTypeDoesNotExistException(simulation_id, agent_type)

        if message_list and message_type and property_:
            ...
        elif message_list and message_type:
            ...
        elif message_list and property_ == "length":
            ...
        elif message_type and property_:
            ...
        elif connection_list and property_ == "length":
            ...
        elif property_:
            return await self._get_agent_type_property(
                simulation_id, agent_type, property_
            )
        else:
            raise InvalidAgentTypeStatisticsRequestException(
                simulation_id,
                agent_type,
                property_,
                message_list,
                message_type,
                connection_list,
            )
