from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from src.db.repositories.backup import BackupRepository
from src.exceptions import (
    SimulationBackupAlreadyExistsException,
    SimulationBackupDoesNotExistException,
)
from src.models import CreateAgent
from src.services.base import BaseService

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_SERVICES_BACKUP", "INFO"))


class BackupService(BaseService):
    repository_type = BackupRepository

    @property
    def repository(self) -> repository_type:
        return self._repository

    def _get_initial_properties(
        self, agent: CreateAgent, simulation_id: str
    ) -> Dict[str, str | float]:
        return {
            "simulation_id": simulation_id,
            "jid": agent.jid,
            "type": agent.type,
        }

    def _get_initial_connections(
        self, agent: CreateAgent
    ) -> Dict[str, str | List[str]]:
        return {
            "from": agent.jid,
            "to": agent.connections,
        }

    async def create_backup(
        self, simulation_id: str, agent_data: List[CreateAgent]
    ) -> None:
        if await self.repository.simulation_exists(simulation_id):
            raise SimulationBackupAlreadyExistsException(simulation_id)

        agents_properties = []
        agents_initial_connections = []
        for agent in agent_data:
            agents_properties.append(self._get_initial_properties(agent, simulation_id))
            agents_initial_connections.append(self._get_initial_connections(agent))

        await self.repository.create_agents(
            agents_properties, agents_initial_connections
        )

    async def delete_backup(self, simulation_id: str) -> None:
        if not await self.repository.simulation_exists(simulation_id):
            raise SimulationBackupDoesNotExistException(simulation_id)

        await self.repository.delete_agents(simulation_id)

    async def get_backup(self, simulation_id: str) -> List[Dict[str, Any]]:
        if not await self.repository.simulation_exists(simulation_id):
            raise SimulationBackupDoesNotExistException(simulation_id)

        (
            agent_records,
            relationship_records,
        ) = await self.repository.get_agents_and_relationships(simulation_id)

        agents = {}
        id_to_jid = {}
        for record in agent_records:
            agent = dict(record["agent"])
            del agent["simulation_id"]
            agents[agent["jid"]] = agent
            id_to_jid[record["agent"].id] = agent["jid"]

        for record in relationship_records:
            properties = dict(record["relationship"].items())
            r_type = properties.get("r_type", None)
            property_name = record["relationship"].type
            from_jid = id_to_jid[record["relationship"].start_node.id]
            to_jid = id_to_jid[record["relationship"].end_node.id]

            if property_name not in agents[from_jid]:
                agents[from_jid][property_name] = []

            if r_type == "connection":
                agents[from_jid][property_name].append(to_jid)
            else:
                agents[from_jid][property_name].append(properties)

        return list(agents.values())
