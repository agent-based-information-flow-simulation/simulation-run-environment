from __future__ import annotations

from typing import TYPE_CHECKING

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
        get_agent_type_property = """
        MATCH (agent:Agent {simulation_id: $simulation_id, type: $agent_type})
        RETURN COLLECT(agent[$property]) AS property
        """

        records = await self.session.run(
            get_agent_type_property,
            simulation_id=simulation_id,
            agent_type=agent_type,
            property=property_,
        )

        return await records.single()
