from __future__ import annotations

from collections import Counter
from typing import Any, List

import numpy as np

from src.db.repositories.statistics import StatisticsRepository
from src.exceptions import (
    AgentTypeDoesNotExistException,
    InconsistentListDataTypesException,
    InvalidAgentTypeStatisticsRequestException,
    InvalidMessageTypeStatisticsRequestException,
    MessageTypeDoesNotExistException,
    SimulationBackupDoesNotExistException,
)
from src.models import Statistics
from src.services.base import BaseService


class StatisticsService(BaseService):
    repository_type = StatisticsRepository

    @property
    def repository(self) -> repository_type:
        return self._repository

    def _get_numerical_statistics(self, data: List[int | float]) -> Statistics:
        histogram, bin_edges = np.histogram(data)

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
        elif all(
            isinstance(item, list)
            and all([isinstance(subitem, (int, float)) for subitem in item])
            for item in data
        ):
            return self._get_numerical_statistics(
                [element for sublist in data for element in sublist]
            )
        else:
            raise InconsistentListDataTypesException(
                simulation_id, agent_type, property_, data
            )

    async def _get_agent_type_relationship_list_length(
        self, simulation_id: str, agent_type: str, list_name: str
    ) -> Statistics:
        agent_type_relationship_list_length_records = (
            await self.repository.get_agent_type_relationship_list_length(
                simulation_id, agent_type, list_name
            )
        )
        data: List[int] = [
            record["list_length"]
            for record in agent_type_relationship_list_length_records
        ]
        return self._get_numerical_statistics(data)

    async def _get_agent_type_message_type_count_in_message_list(
        self, simulation_id: str, agent_type: str, message_list: str, message_type: str
    ) -> Statistics:
        agent_type_message_type_count_in_message_list_records = (
            await self.repository.get_agent_type_message_type_count_in_message_list(
                simulation_id, agent_type, message_list, message_type
            )
        )
        data: List[int] = [
            record["message_list_length"]
            for record in agent_type_message_type_count_in_message_list_records
        ]
        return self._get_numerical_statistics(data)

    async def _get_agent_type_message_type_property_in_message_list(
        self,
        simulation_id: str,
        agent_type: str,
        message_list: str,
        message_type: str,
        property_: str,
    ) -> Statistics:
        agent_type_message_property_in_message_list_records = (
            await self.repository.get_agent_type_message_type_property_in_message_list(
                simulation_id, agent_type, message_list, message_type, property_
            )
        )
        data: List[Any] = [
            record["property"]
            for record in agent_type_message_property_in_message_list_records
        ]
        if all(isinstance(item, (int, float)) for item in data):
            return self._get_numerical_statistics(data)
        elif all(isinstance(item, str) for item in data):
            return self._get_categorical_statistics(data)
        else:
            raise InconsistentListDataTypesException(
                simulation_id, agent_type, property_, data
            )

    async def _get_agent_type_message_type_property_in_all_message_lists(
        self,
        simulation_id: str,
        agent_type: str,
        message_type: str,
        property_: str,
    ) -> Statistics:
        agent_type_message_type_property_in_all_message_lists_records = await self.repository.get_agent_type_message_type_property_in_all_message_lists(
            simulation_id, agent_type, message_type, property_
        )
        data: List[Any] = [
            record["property"]
            for record in agent_type_message_type_property_in_all_message_lists_records
        ]
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
            return await self._get_agent_type_message_type_property_in_message_list(
                simulation_id, agent_type, message_list, message_type, property_
            )
        elif message_list and message_type:
            return await self._get_agent_type_message_type_count_in_message_list(
                simulation_id, agent_type, message_list, message_type
            )
        elif message_list and property_ == "length":
            return await self._get_agent_type_relationship_list_length(
                simulation_id, agent_type, message_list
            )
        elif message_type and property_:
            return (
                await self._get_agent_type_message_type_property_in_all_message_lists(
                    simulation_id, agent_type, message_type, property_
                )
            )
        elif connection_list and property_ == "length":
            return await self._get_agent_type_relationship_list_length(
                simulation_id, agent_type, connection_list
            )
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

    async def _get_message_type_property(
        self, simulation_id: str, message_type: str, property_: str
    ) -> Statistics:
        message_type_property_record = await self.repository.get_message_type_property(
            simulation_id, message_type, property_
        )
        data: List[Any] = [
            record["property"] for record in message_type_property_record
        ]
        if all(isinstance(item, (int, float)) for item in data):
            return self._get_numerical_statistics(data)
        elif all(isinstance(item, str) for item in data):
            return self._get_categorical_statistics(data)
        else:
            raise InconsistentListDataTypesException(
                simulation_id, message_type, property_, data
            )

    async def get_message_type_statistics(
        self,
        simulation_id: str,
        message_type: str,
        property_: str,
    ) -> Statistics:
        if not await self.repository.simulation_exists(simulation_id):
            raise SimulationBackupDoesNotExistException(simulation_id)

        if not await self.repository.message_type_exists(simulation_id, message_type):
            raise MessageTypeDoesNotExistException(simulation_id, message_type)

        if property_:
            return await self._get_message_type_property(
                simulation_id, message_type, property_
            )
        else:
            raise InvalidMessageTypeStatisticsRequestException(
                simulation_id,
                message_type,
                property_,
            )
