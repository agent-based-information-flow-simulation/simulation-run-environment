from __future__ import annotations

from typing import Any, List


class SimulationBackupAlreadyExistsException(Exception):
    def __init__(self, simulation_id: str):
        super().__init__(f"[simulation {simulation_id}] Backup already exists")


class SimulationBackupDoesNotExistException(Exception):
    def __init__(self, simulation_id: str):
        super().__init__(f"[simulation {simulation_id}] Backup does not exist")


class AgentTypeDoesNotExistException(Exception):
    def __init__(self, simulation_id: str, agent_type: str):
        super().__init__(
            f"[simulation {simulation_id}] Agent type {agent_type} does not exist"
        )
        
        
class MessageTypeDoesNotExistException(Exception):
    def __init__(self, simulation_id: str, message_type: str):
        super().__init__(
            f"[simulation {simulation_id}] Message type {message_type} does not exist"
        )


class InconsistentListDataTypesException(Exception):
    def __init__(
        self, simulation_id: str, agent_type: str, property_: str, data: List[Any]
    ):
        super().__init__(
            f"[simulation {simulation_id}] Agent type {agent_type} property {property_} has inconsistent data types: {data}"
        )


class InvalidAgentTypeStatisticsRequestException(Exception):
    def __init__(
        self,
        simulation_id: str,
        agent_type: str,
        property_: str,
        message_list: str,
        message_type: str,
        connection_list: str,
    ):
        super().__init__(
            f"[simulation {simulation_id}] Invalid statistics request for agent type {agent_type}, property {property_}, message list {message_list}, message type {message_type}, connection list {connection_list}"
        )
