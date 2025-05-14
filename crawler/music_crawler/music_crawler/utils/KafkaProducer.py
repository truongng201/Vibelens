import json
from confluent_kafka import Producer


class KafkaProducer:
    def __init__(self, topic, bootstrap_servers='kafka:29092'):
        self.topic = topic
        self.producer = Producer({'bootstrap.servers': bootstrap_servers})

    def _delivery_report(self, err, msg):
        if err is not None:
            print(f"❌ Delivery failed for message {msg.value()}: {err}")
        else:
            print(f"✅ Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

    def send(self, message: dict):
        try:
            json_value = json.dumps(message).encode('utf-8')
            self.producer.produce(
                topic=self.topic,
                value=json_value,
                callback=self._delivery_report
            )
            self.producer.poll(0)
        except Exception as e:
            print(f"⚠️ Failed to send message: {e}")

    def flush(self):
        """Flush any buffered messages before exiting."""
        self.producer.flush()
