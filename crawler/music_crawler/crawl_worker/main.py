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
    "crawl_worker.tasks.crawl_songs_hopamchuan",
]
CRAWL_INTERVAL_TIME = int(os.getenv('CRAWL_INTERVAL_TIME', 60 * 60 * 3))
CELERY_BEAT_SCHEDULE = {
    f'crawl-songs-every-{CRAWL_INTERVAL_TIME}-seconds': {
        'task': "crawl_songs_hopamchuan",    
        'schedule': timedelta(seconds=CRAWL_INTERVAL_TIME), 
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