import os
import time
from KafkaConsumer import KafkaConsumer
from KafkaProducer import KafkaProducer
from YtbDownloader import download_ytb_mp3
from MinioDB import MinioDB
from logger import logger

RETRY_DELAY = 10
MAX_RETRIES = 5
FAILED_TOPIC = os.getenv("RETRY_KAFKA_TOPIC", "failed-downloads")
DELAY_DOWNLOAD_TIME = int(os.getenv("DELAY_DOWNLOAD_TIME", 30)) # 30 seconds

minio_client = MinioDB()
consumer = KafkaConsumer()
producer = KafkaProducer(topic=FAILED_TOPIC)  # 🔄 YOUR KafkaProducer setup

def callback(payload):
    title = payload.get("title")
    artist = payload.get("artist")
    song_id = payload.get("id")

    if not title or not artist or not song_id:
        logger.warning(f"⛔ Invalid payload received: {payload}")
        _send_to_failed_topic(payload, reason="missing required fields")
        return

    retries = 0
    while retries < MAX_RETRIES:
        try:
            logger.info(f"🎶 Processing: {title} by {artist} (ID: {song_id})")

            # Step 1: Download
            file_path = download_ytb_mp3(title, artist, song_id)
            logger.info(f"✅ Downloaded: {file_path}")

            # Step 2: Upload
            minio_client.upload_mp3(
                file_path=file_path,
                object_name=song_id
            )
            logger.info(f"📤 Uploaded to MinIO as object: {song_id}")

            # Step 3: Clean up
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🧹 Removed local file: {file_path}")
            time.sleep(DELAY_DOWNLOAD_TIME) # Delay to avoid overwhelming the server
            break  # ✅ Success

        except Exception as e:
            retries += 1
            logger.error(f"❌ Error processing {title} by {artist} (ID: {song_id}), retry {retries}/{MAX_RETRIES} - {e}")
            time.sleep(RETRY_DELAY)

    if retries == MAX_RETRIES:
        logger.error(f"🚨 Max retries reached. Sending to failed topic: {payload}")
        _send_to_failed_topic(payload, reason="max retries exceeded")


def _send_to_failed_topic(payload, reason):
    try:
        payload_with_error = payload.copy()
        payload_with_error["error_reason"] = reason
        producer.send(payload_with_error)
        logger.info(f"📨 Sent to failed topic '{FAILED_TOPIC}': {payload_with_error}")
    except Exception as e:
        logger.critical(f"🔥 Failed to send to dead-letter topic '{FAILED_TOPIC}': {e}")


# Start consumer
logger.info("📡 Starting Kafka consumer...")
try:
    consumer.retrieve_data(callback=callback)
finally:
    producer.flush()  # Ensure all messages are sent before shutdown
