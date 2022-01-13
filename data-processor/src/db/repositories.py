from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from neo4j._async.work.transaction import AsyncTransaction
from neo4j.data import Record

if TYPE_CHECKING:
    from neo4j import AsyncSession


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session


class SimulationRepository(BaseRepository):
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
        create_agents_query = """
        UNWIND $agents_properties AS agent_properties
        CREATE (agent:Agent)
        SET agent += agent_properties
        """
        create_initial_connections_query = """
        UNWIND $agents_initial_connections AS connection
        MATCH (from_agent:Agent {jid: connection.from})
        UNWIND connection.to as to
        MATCH (to_agent:Agent {jid: to})
        CREATE (from_agent)-[:connections {r_type: "connection"}]->(to_agent)
        """
        await self.session.run(create_jid_index_query)
        await self.session.run(create_simulation_id_index_query)
        tx = await self.session.begin_transaction()
        await tx.run(create_agents_query, agents_properties=agents_properties)
        await tx.run(
            create_initial_connections_query,
            agents_initial_connections=agents_initial_connections,
        )
        await tx.commit()
        await tx.close()

    async def update_agent(
        self,
        jid: str,
        properties: List[Dict[str, float | str]],
        connections: List[Dict[str, str | List[str]]],
        messages: List[Dict[str, str | List[str]]],
    ) -> None:
        replace_all_properties_query = """
        MERGE (agent:Agent {jid: $jid})
        SET agent = $properties
        """
        remove_all_relationships_query = """
        MATCH (from_agent:Agent {jid: $jid})
        MATCH (from_agent)-[relationship]->()
        DELETE relationship
        """
        add_all_connections_query = """
        MATCH (from_agent:Agent {jid: $jid})
        UNWIND $connections as connections
        WITH from_agent, connections.name AS connection_name, connections.to as connections_to
        UNWIND connections_to as to
        MATCH (to_agent:Agent {jid: to})
        CALL apoc.create.relationship(from_agent, connection_name, {r_type: "connection"}, to_agent) YIELD rel
        RETURN NULL
        """
        add_all_messages_query = """
        MATCH (from_agent:Agent {jid: $jid})
        UNWIND $messages as message_list
        WITH from_agent, message_list.name AS message_list_name, message_list.messages as message_list_messages
        UNWIND message_list_messages as message
        MATCH (to_agent:Agent {jid: message.sender})
        CALL apoc.create.relationship(from_agent, message_list_name, message, to_agent) YIELD rel
        RETURN NULL
        """
        tx = await self.session.begin_transaction()
        await tx.run(replace_all_properties_query, jid=jid, properties=properties)
        await tx.run(remove_all_relationships_query, jid=jid)
        await tx.run(
            add_all_connections_query,
            jid=jid,
            connections=connections,
        )
        await tx.run(
            add_all_messages_query,
            jid=jid,
            messages=messages,
        )
        await tx.commit()
        await tx.close()

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
