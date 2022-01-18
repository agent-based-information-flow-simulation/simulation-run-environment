from __future__ import annotations

import asyncio
import logging
import os
import uuid
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict, List

import orjson
import uvloop
from aiokafka import AIOKafkaConsumer
from neo4j import AsyncGraphDatabase

from src.settings import configure_logging, settings

if TYPE_CHECKING:  # pragma: no cover
    from aiokafka import ConsumerRecord, TopicPartition
    from neo4j import AsyncNeo4jDriver

logger = logging.getLogger(__name__)
logger.setLevel(level=os.environ.get("LOG_LEVEL_MAIN", "INFO"))


class Consumer:
    def __init__(
        self, db_url: str, kafka_address: str, topic: str, batch_timeout_ms: int
    ):
        self.db_url = db_url
        self.kafka_address = kafka_address
        self.topic = topic
        self.batch_timeout_ms = batch_timeout_ms
        self.kafka: AIOKafkaConsumer | None = None
        self.db: AsyncNeo4jDriver | None = None
        self.cleanup_functions = []

    def register_cleanup_function(
        self, cleanup_function: Callable[[], Coroutine[Any, Any, None]]
    ) -> None:
        self.cleanup_functions.append(cleanup_function)

    async def connect_to_kafka(self) -> None:
        logger.info("Connecting to kafka")
        kafka = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.kafka_address,
            client_id=f"agent_updates_consumer_{uuid.uuid4()}",
            group_id="agent_updates_consumer_group",
            key_deserializer=lambda k: k.decode("utf-8"),
            value_deserializer=orjson.loads,
        )
        await kafka.start()
        self.kafka = kafka
        logger.info("Connected to kafka")
        self.register_cleanup_function(self.disconnect_from_kafka)

    async def disconnect_from_kafka(self) -> None:
        logger.info("Disconnecting from kafka")
        await self.kafka.stop()
        logger.info("Disconnected from kafka")

    def connect_to_db(self) -> None:
        logger.info("Connecting to database")
        self.db = AsyncGraphDatabase.driver(self.db_url, keep_alive=True)
        logger.info("Connected to database")
        self.register_cleanup_function(self.disconnect_from_db)

    async def disconnect_from_db(self) -> None:
        logger.info("Disconnecting from database")
        await self.db.close()
        logger.info("Disconnected from database")

    async def cleanup(self) -> None:
        logger.info("Cleaning up")
        for cleanup_function in self.cleanup_functions:
            await cleanup_function()

    async def save_agent_updates_in_db(self, batch: List[Dict[str, Any]]) -> None:
        query = """
        UNWIND $batch AS event
        MATCH (agent:Agent {jid: event.properties.jid, simulation_id: event.properties.simulation_id})
        OPTIONAL MATCH (agent)-[relationship]->()
        SET agent = event.properties
        DELETE relationship
        
        WITH DISTINCT agent, event
        UNWIND event.connections as connection_list
        WITH agent, connection_list.name AS connection_list_name, connection_list.to as connection_list_to, event
        UNWIND connection_list_to as to
        MATCH (to_agent:Agent {jid: to, simulation_id: event.properties.simulation_id})
        CALL apoc.create.relationship(agent, connection_list_name, {r_type: 'connection'}, to_agent) YIELD rel
        
        WITH DISTINCT agent, event
        UNWIND event.messages as message_list
        WITH agent, message_list.name AS message_list_name, message_list.messages as message_list_messages, event
        UNWIND message_list_messages as message
        MATCH (to_agent:Agent {jid: message.sender, simulation_id: event.properties.simulation_id})
        CALL apoc.create.relationship(agent, message_list_name, message, to_agent) YIELD rel
        RETURN NULL
        """
        async with self.db.session() as session:
            await session.run(query, batch=batch)

    async def get_agent_updates(self) -> List[Dict[str, Any]]:
        batch: Dict[TopicPartition, List[ConsumerRecord]] = await self.kafka.getmany(
            timeout_ms=self.batch_timeout_ms
        )
        record_lists: List[List[ConsumerRecord]] = list(batch.values())
        if record_lists:
            record_list = record_lists[0]
            return [record.value for record in record_list]
        return []

    async def consume(self) -> None:
        while True:
            agent_updates = await self.get_agent_updates()
            if agent_updates:
                await self.save_agent_updates_in_db(agent_updates)
                logger.info(f"Consumed {len(agent_updates)} agent updates")

    async def start(self) -> None:
        try:
            self.connect_to_db()
            await self.connect_to_kafka()
            await self.consume()
        finally:
            await self.cleanup()


def main() -> None:
    configure_logging()
    uvloop.install()
    asyncio.run(
        Consumer(
            settings.db_url,
            settings.kafka_address,
            settings.topic,
            settings.batch_timeout_ms,
        ).start()
    )


if __name__ == "__main__":
    main()
