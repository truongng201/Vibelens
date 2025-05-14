from celery import Celery
import os
from datetime import timedelta
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_DB = os.getenv('REDIS_DB', '0')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'secret')
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
CELERY_TASK_LIST = [
    "crawl_worker.tasks.crawl_songs",
]
CRAWL_INTERVAL_TIME = os.getenv('CRAWL_INTERVAL_TIME', '3') # in hours
DEFAULT_INTERVAL_TIME_IN_SECOND = 15
CELERY_BEAT_SCHEDULE = {
    'crawl-songs-every-minutes': {
        'task': "crawl_songs",    
        'schedule': timedelta(seconds=DEFAULT_INTERVAL_TIME_IN_SECOND),  # Every 15 seconds
        'args': (),
    },
}
# Initialize Celery with Redis as the broker
def create_celery_app(module):
    celery = Celery(module,broker=REDIS_URL,include=CELERY_TASK_LIST)
    
    celery.conf.beat_schedule = CELERY_BEAT_SCHEDULE
    celery.conf.timezone = 'UTC'
    
    return celery

app = create_celery_app('crawl_worker')
logger.info("Celery worker initialized.")