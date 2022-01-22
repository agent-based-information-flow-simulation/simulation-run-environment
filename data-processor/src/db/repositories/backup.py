from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple

from src.db.repositories.base import BaseRepository

if TYPE_CHECKING:
    from neo4j.data import Record


class BackupRepository(BaseRepository):
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

    async def create_agents(
        self,
        agents_properties: List[Dict[str, float | str]],
        agents_initial_connections: List[Dict[str, str | List[str]]],
    ) -> None:
        create_jid_index_query = """
        CREATE INDEX idx_jid IF NOT EXISTS FOR (agent:Agent) on (agent.jid)
        """

        create_simulation_id_index_query = """
        CREATE INDEX idx_simulation_id IF NOT EXISTS FOR (agent:Agent) on (agent.simulation_id)
        """

        create_type_index_query = """
        CREATE INDEX idx_type IF NOT EXISTS FOR (agent:Agent) on (agent.type)
        """

        create_agents_query = """
        UNWIND $agents_properties AS agent_properties
        CREATE (agent:Agent)
        SET agent += agent_properties

        WITH COUNT(*) AS dummy

        UNWIND $agents_initial_connections AS connection
        MATCH (from_agent:Agent {jid: connection.from})
        UNWIND connection.to as to
        MATCH (to_agent:Agent {jid: to})
        CREATE (from_agent)-[:connections {r_type: "connection"}]->(to_agent)
        """

        await self.session.run(create_jid_index_query)
        await self.session.run(create_simulation_id_index_query)
        await self.session.run(create_type_index_query)
        await self.session.run(
            create_agents_query,
            agents_properties=agents_properties,
            agents_initial_connections=agents_initial_connections,
        )

    async def delete_agents(self, simulation_id: str) -> None:
        delete_all_agents_from_simulation_query = """
        MATCH (agent:Agent {simulation_id: $simulation_id})
        DETACH DELETE agent
        """

        await self.session.run(
            delete_all_agents_from_simulation_query, simulation_id=simulation_id
        )

    async def get_agents_and_relationships(
        self, simulation_id: str
    ) -> Tuple[List[Record], List[Record]]:
        get_agents_query = """
        MATCH (agent:Agent {simulation_id: $simulation_id})
        RETURN agent
        """

        get_relationships_query = """
        MATCH (agent:Agent {simulation_id: $simulation_id})-[relationship]->()
        RETURN relationship
        """

        tx = await self.session.begin_transaction()
        agent_records = await tx.run(get_agents_query, simulation_id=simulation_id)
        relationships_records = await tx.run(
            get_relationships_query, simulation_id=simulation_id
        )
        agents = [record async for record in agent_records]
        relationships = [record async for record in relationships_records]
        await tx.commit()
        await tx.close()

        return agents, relationships
