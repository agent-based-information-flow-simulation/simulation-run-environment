from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict, List

import orjson
import uvloop
from aiokafka import AIOKafkaConsumer
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from pymongo.errors import CollectionInvalid

from src.settings import configure_logging, settings

if TYPE_CHECKING:  # pragma: no cover
    from aiokafka import ConsumerRecord, TopicPartition
    from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase


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
        self.db_client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self.collection: AsyncIOMotorCollection | None = None
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
            client_id=f"agent_updates_consumer_mongo_{uuid.uuid4()}",
            group_id="agent_updates_consumer_mongo_group",
            key_deserializer=lambda k: k.decode("utf-8"),
            value_deserializer=orjson.loads,
        )
        await kafka.start()
        self.kafka = kafka
        logger.info("Connected to kafka")
        self.register_cleanup_function(self.disconnect_from_kafka)

    async def disconnect_from_kafka(self) -> None:
        logger.info("Disconnecting from kafka")
        if self.kafka:
            await self.kafka.stop()
        logger.info("Disconnected from kafka")

    def connect_to_db(self) -> None:
        logger.info("Connecting to the database")
        self.db_client = AsyncIOMotorClient(self.db_url)
        logger.info("Connected to the database")
        self.register_cleanup_function(self.disconnect_from_db)

    async def disconnect_from_db(self) -> None:
        logger.info("Disconnecting from the database")
        if self.db_client:
            self.db_client.close()
        logger.info("Disconnected from the database")

    def access_db(self) -> None:
        logger.info("Accessing the database")
        self.db = self.db_client.get_database("simulations")
        logger.info("Accessed the database")

    async def access_collection(self) -> None:
        logger.info("Accessing the collection")
        try:
            self.collection = await self.db.create_collection(
                "agents", timeseries={"timeField": "timestamp", "metaField": "metadata"}
            )
        except CollectionInvalid:
            logger.warning("Collection already exists")
            self.collection = self.db["agents"]
        logger.info("Accessed the collection")

    async def create_indexes(self) -> None:
        logger.info("Creating indexes for the collection")
        await self.collection.create_index(
            [
                ("timestamp", ASCENDING),
                ("metadata.jid", ASCENDING),
                ("metadata.simulation_id", ASCENDING),
            ]
        )
        logger.info("Created indexes for the collection")

    async def cleanup(self) -> None:
        logger.info("Cleaning up")
        for cleanup_function in self.cleanup_functions:
            await cleanup_function()

    async def save_agent_updates_in_db(self, batch: List[Dict[str, Any]]) -> None:
        data = [
            {
                "timestamp": datetime.utcnow(),
                "metadata": {
                    "jid": agent["jid"],
                    "simulation_id": agent["simulation_id"],
                },
                "agent": agent,
            }
            for agent in batch
        ]
        result = await self.collection.insert_many(data)
        logger.info(
            f"Saved {len(result.inserted_ids)} agent updates (acknowledged: {result.acknowledged})"
        )

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
            self.access_db()
            await self.access_collection()
            await self.create_indexes()
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
