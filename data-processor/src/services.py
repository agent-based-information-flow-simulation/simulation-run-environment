from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Tuple, Type

from neo4j.exceptions import TransientError

from src.db.repositories import BaseRepository, SimulationRepository
from src.exceptions import SimulationBackupAlreadyExistsException
from src.models import CreateAgent, UpdateAgent

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_SERVICES", "INFO"))


class BaseService:
    repository_type: Type[BaseRepository] = BaseRepository

    def __init__(self, repository: BaseRepository) -> None:
        self._repository = repository

    @property
    def repository(self) -> repository_type:
        ...


class SimulationService(BaseService):
    repository_type = SimulationRepository

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

    def _get_properties(
        self, agent: UpdateAgent, simulation_id: str
    ) -> Dict[str, str | float]:
        return {
            "simulation_id": simulation_id,
            "jid": agent.jid,
            "type": agent.type,
            **agent.floats,
            **agent.enums,
        }

    def _get_connections(self, agent: UpdateAgent) -> List[Dict[str, str | List[str]]]:
        connections = []
        for connection_name, to_jids in agent.connections.items():
            connections.append({"name": connection_name, "to": to_jids})
        return connections

    def _get_messages(self, agent: UpdateAgent) -> List[Dict[str, str | List[str]]]:
        messages = []
        for message_list_name, message_list in agent.messages.items():
            messages.append({"name": message_list_name, "messages": message_list})
        return messages

    async def update_agent(self, simulation_id: str, agent: UpdateAgent) -> None:
        properties = self._get_properties(agent, simulation_id)
        connections = self._get_connections(agent)
        messages = self._get_messages(agent)

        max_retires = 3
        retries = 0
        while retries < max_retires:
            try:
                await self.repository.update_agent(
                    agent.jid, properties, connections, messages
                )
            except TransientError as e:
                retries += 1
                retries_left = max_retires - retries
                logger.warning(
                    f"[{agent.jid}] Database transient error ({retries_left} retires left): {e}"
                )
                if retries_left == 0:
                    logger.error(
                        f"[{agent.jid}] Database transient error - no more retires left: {e}"
                    )
                else:
                    await asyncio.sleep(0.02)
                continue
            break

    async def delete_backup(self, simulation_id: str) -> None:
        await self.repository.delete_agents(simulation_id)

    async def get_backup(self, simulation_id: str) -> List[Dict[str, Any]]:
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
