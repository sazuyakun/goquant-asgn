"""Kafka client module to create and configure a Kafka producer."""

import json
import logging
import time

from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

KAFKA_BOOTSTRAP_SERVERS = ["localhost:9092"]
logger = logging.getLogger(__name__)


def get_kafka_producer(retries=5, delay=5) -> KafkaProducer:
    """
    Create and return a Kafka producer instance.
    """
    for attempt in range(retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=5,
                linger_ms=10,
                batch_size=32 * 1024,
            )
            logger.info("Kafka producer created successfully.")
            return producer
        except NoBrokersAvailable:
            logger.warning(
                "Kafka brokers not available. Retrying in %ss... (Attempt %s/%s)",
                delay,
                attempt + 1,
                retries,
            )
            time.sleep(delay)
    logger.error("Failed to create Kafka producer after all attempts.")
    raise NoBrokersAvailable("Could not connect to Kafka brokers.")


def get_kafka_consumer(topic: str, group_id: str, retries=5, delay=5) -> KafkaConsumer:
    """
    Create and return a Kafka consumer instance.
    """
    for attempt in range(retries):
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset="earliest",  # Beginning of the topic
                group_id=group_id,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            )
            logger.info(
                "Kafka consumer created successfully for topic: %s with group_id: %s",
                topic,
                group_id,
            )
            return consumer
        except NoBrokersAvailable:
            logger.warning(
                "Kafka brokers not available. Retrying in %ss... (Attempt %s/%s)",
                delay,
                attempt + 1,
                retries,
            )
            time.sleep(delay)
    logger.error("Failed to create Kafka consumer after all attempts.")
    raise NoBrokersAvailable("Could not connect to Kafka brokers.")
