import logging
import os


def configure_logging() -> None:
    logging.basicConfig(format="%(levelname)s:     [%(name)s] %(message)s")


class Settings:
    db_url = os.getenv("DB_URL", "")
    kafka_address = os.getenv("KAFKA_ADDRESS", "")
    topic = os.getenv("UPDATE_AGENT_INPUT_TOPIC_NAME", "")
    batch_timeout_ms = int(os.getenv("BATCH_TIMEOUT_MS", "1000"))


settings = Settings()
