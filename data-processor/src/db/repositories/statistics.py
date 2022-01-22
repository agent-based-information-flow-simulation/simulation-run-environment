from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.db.repositories.base import BaseRepository

if TYPE_CHECKING:
    from neo4j.data import Record


class StatisticsRepository(BaseRepository):
    async def simulation_exists(self, simulation_id: str) -> bool:
        get_single_agent_from_simulation_query = """
        MATCH (agent:Agent {simulation_id: $simulation_id})
        RETURN agent
        LIMIT 1
        """

        records = await self.session.run(
            get_single_agent_from_simulation_query, simulation_id=simulation_id
        )

        return len([record async for record in records]) != 0

    async def agent_type_exists(self, simulation_id: str, agent_type: str) -> bool:
        get_single_agent_type_from_simulation_query = """
        MATCH (agent:Agent {simulation_id: $simulation_id, type: $agent_type})
        RETURN agent
        LIMIT 1
        """

        records = await self.session.run(
            get_single_agent_type_from_simulation_query,
            simulation_id=simulation_id,
            agent_type=agent_type,
        )

        return len([record async for record in records]) != 0

    async def get_agent_type_property(
        self, simulation_id: str, agent_type: str, property_: str
    ) -> Record | None:
        get_agent_type_property_query = """
        MATCH (agent:Agent {simulation_id: $simulation_id, type: $agent_type})
        RETURN COLLECT(agent[$property]) AS property
        """

        records = await self.session.run(
            get_agent_type_property_query,
            simulation_id=simulation_id,
            agent_type=agent_type,
            property=property_,
        )

        return await records.single()

    async def get_agent_type_list_length(
        self, simulation_id: str, agent_type: str, list_name: str
    ) -> List[Record]:
        get_agent_type_list_length_query = """
        MATCH (agent:Agent {simulation_id: $simulation_id, type: $agent_type})
        OPTIONAL MATCH (agent)-[relationship]->() WHERE TYPE(relationship) = $relationship_name
        WITH agent, COUNT(relationship) AS relationship_count
        RETURN relationship_count
        ORDER BY relationship_count
        """

        records = await self.session.run(
            get_agent_type_list_length_query,
            simulation_id=simulation_id,
            agent_type=agent_type,
            relationship_name=list_name,
        )

        return [record async for record in records]

    async def get_agent_type_message_type_count_in_message_list(
        self, simulation_id: str, agent_type: str, message_list: str, message_type: str
    ) -> List[Record]:
        get_agent_type_message_type_count_in_message_list_query = """
        MATCH (agent:Agent {simulation_id: $simulation_id, type: $agent_type})
        OPTIONAL MATCH (agent)-[relationship {type: $message_type}]->() WHERE TYPE(relationship) = $relationship_name
        WITH agent, COUNT(relationship) AS relationship_count
        RETURN relationship_count
        ORDER BY relationship_count
        """

        records = await self.session.run(
            get_agent_type_message_type_count_in_message_list_query,
            simulation_id=simulation_id,
            agent_type=agent_type,
            relationship_name=message_list,
            message_type=message_type,
        )

        return [record async for record in records]

    async def get_agent_type_message_type_property_in_message_list(
        self,
        simulation_id: str,
        agent_type: str,
        message_list: str,
        message_type: str,
        property_: str,
    ) -> List[Record]:
        get_agent_type_message_property_in_message_list_query = """
        MATCH (agent:Agent {simulation_id: $simulation_id, type: $agent_type})-[message {type: $message_type}]->() WHERE TYPE(message) = $message_list
        RETURN message[$property] as property
        ORDER BY property
        """

        records = await self.session.run(
            get_agent_type_message_property_in_message_list_query,
            simulation_id=simulation_id,
            agent_type=agent_type,
            message_list=message_list,
            message_type=message_type,
            property=property_,
        )

        return [record async for record in records]
