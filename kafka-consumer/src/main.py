from __future__ import annotations

import asyncio
import atexit
import logging
import os
from typing import Dict, List

import orjson
from aiokafka import AIOKafkaConsumer
from neo4j import AsyncGraphDatabase

DB_URL = os.getenv("DB_URL", "")
KAFKA_ADDRESS = os.getenv("KAFKA_ADDRESS", "")
TOPIC = os.getenv("UPDATE_AGENT_OUTPUT_TOPIC_NAME", "")

logging.basicConfig(format="%(levelname)s:     [%(name)s] %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_MAIN", "INFO"))


class Consumer:
    def __init__(self):
        self.db_url = DB_URL
        self.kafka_address = KAFKA_ADDRESS
        self.topic = TOPIC
        self.kafka = None
        self.db = None

    async def connect_to_kafka(self) -> None:
        logger.info("Connecting to kafka")
        kafka = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.kafka_address,
            client_id="agent_updates_consumer_0",
            group_id="agent_updates_consumer_group",
            key_deserializer=lambda k: k.decode("utf-8"),
            value_deserializer=orjson.loads,
        )
        await kafka.start()
        self.kafka = kafka
        logger.info("Connected to kafka")

    async def disconnect_from_kafka(self) -> None:
        logger.info("Disconnecting from kafka")
        await self.kafka.stop()
        logger.info("Disconnected from kafka")

    def connect_to_db(self) -> None:
        logger.info("Connecting to database")
        self.db = AsyncGraphDatabase.driver(
            self.db_url, keep_alive=True, max_connection_pool_size=1000
        )
        logger.info("Connected to database")

    async def disconnect_from_db(self) -> None:
        logger.info("Disconnecting from database")
        await self.db.close()
        logger.info("Disconnected from database")

    async def save_agent_update_in_db(
        self,
        simulation_id: str,
        jid: str,
        properties: Dict,
        connections: List,
        messages: List,
    ) -> None:
        query = """
        MATCH (agent:Agent {jid: $jid, simulation_id: $simulation_id})-[relationship]->()
        OPTIONAL MATCH (agent)-[relationship]->()
        SET agent = event.properties
        DELETE relationship        

        WITH DISTINCT agent
        UNWIND $connections as connection_list
        WITH agent, connection_list.name AS connection_list_name, connection_list.to as connection_list_to
        UNWIND connection_list_to as to
        MATCH (to_agent:Agent {jid: to, simulation_id: $simulation_id})
        CALL apoc.create.relationship(agent, connection_list_name, {r_type: 'connection'}, to_agent) YIELD rel

        WITH DISTINCT agent
        UNWIND $messages as message_list
        WITH agent, message_list.name AS message_list_name, message_list.messages as message_list_messages
        UNWIND message_list_messages as message
        MATCH (to_agent:Agent {jid: message.sender, simulation_id: $simulation_id})
        CALL apoc.create.relationship(agent, message_list_name, message, to_agent) YIELD rel
        RETURN NULL
        """

        async with self.db.session() as session:
            await session.run(
                query,
                simulation_id=simulation_id,
                jid=jid,
                properties=properties,
                connections=connections,
                messages=messages,
            )

    async def consume(self) -> None:
        async for message in self.kafka:
            print(f"Update from {message.key}", flush=True)
            await self.save_agent_update_in_db(
                message.value["properties"]["simulation_id"],
                message.value["properties"]["jid"],
                message.value["properties"],
                message.value["connections"],
                message.value["messages"],
            )

    async def start(self) -> None:
        self.connect_to_db()
        atexit.register(self.disconnect_from_db)
        await self.connect_to_kafka()
        atexit.register(self.disconnect_from_kafka)
        await self.consume()


if __name__ == "__main__":
    asyncio.run(Consumer().start())
