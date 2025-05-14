import os
from datetime import datetime, timedelta
from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient
import json

from logger import logger


class KafkaConsumer:
    def __init__(self):
        self.kafka_uri = os.getenv("KAFKA_URI", "kafka:29092")
        self.topic = os.getenv("KAFKA_TOPIC")
        self.group_id = os.getenv("KAFKA_GROUP_ID", "default-group")

        self.consumer = None
        self.running = True
        self.start_time = None
        self.start_offset = None

        self.__check_kafka_connection()

    def __check_kafka_connection(self):
        try:
            admin = AdminClient({'bootstrap.servers': self.kafka_uri})
            topics = admin.list_topics(timeout=5).topics
            if topics:
                logger.info(f"Connected to Kafka broker at {self.kafka_uri}")
        except Exception as e:
            logger.exception("Kafka connection failed")
            raise ConnectionError from e

    def __init_consumer(self, extra_config=None):
        try:
            config = {
                'bootstrap.servers': self.kafka_uri,
                'group.id': self.group_id,
                'auto.offset.reset': 'earliest',
                'enable.auto.commit': False
            }
            if extra_config:
                config.update(extra_config)

            self.consumer = Consumer(config)
            logger.info("Kafka consumer created successfully.")
        except Exception as e:
            logger.exception("Failed to create Kafka consumer")
            raise ConnectionError from e

    def __format_timestamp(self, timestamp_ms):
        return datetime.fromtimestamp(timestamp_ms / 1000.0) + timedelta(hours=7)

    def __log_message_info(self, msg):
        logger.info("Received message:")
        logger.info(f"Topic: {msg.topic()} | Partition: {msg.partition()} | Offset: {msg.offset()} | Key: {msg.key()}")
        logger.info(f"Produced at: {self.__format_timestamp(msg.timestamp()[1])}")

        if self.start_offset is not None:
            count = msg.offset() - self.start_offset + 1
            logger.info(f"Message count since start: {count}")

        if self.start_time:
            elapsed = datetime.now() + timedelta(hours=7) - self.start_time
            logger.info(f"Elapsed time: {elapsed}")

    def retrieve_data(self, callback=None):
        self.__init_consumer()

        if not self.consumer:
            raise KafkaError("Kafka consumer is not initialized.")

        self.consumer.subscribe([self.topic])
        logger.info(f"Subscribed to topic: {self.topic}")

        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"Partition end: {msg.topic()}-{msg.partition()} offset {msg.offset()}")
                    else:
                        raise KafkaException(msg.error())
                    continue

                if self.start_offset is None:
                    self.start_offset = msg.offset()
                if self.start_time is None:
                    self.start_time = datetime.now() + timedelta(hours=7)

                self.__log_message_info(msg)

                value = msg.value().decode("utf-8") if msg.value() else None
                if value:
                    data = json.loads(value)
                    payload = {
                        **data,
                        "offset": msg.offset(),
                        "key": msg.key().decode("utf-8") if msg.key() else None
                    }

                    if callback:
                        callback(payload)

                try:
                    self.consumer.commit(asynchronous=False)
                except Exception as e:
                    logger.error(f"Commit failed: {e}")

        finally:
            self.consumer.close()
            logger.info("Consumer closed gracefully.")

    def shutdown(self):
        self.running = False
