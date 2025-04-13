from celery import Celery
import os
from functools import wraps
from celery.schedules import crontab
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_DB = os.getenv('REDIS_DB', '0')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
CELERY_TASK_LIST = [
    "crawl_worker.tasks.crawl_songs",
]
CRAWL_INTERVAL_TIME = os.getenv('CRAWL_INTERVAL_TIME', '3') # in hours
DEFAULT_INTERVAL_TIME_IN_SECOND = 15
CELERY_BEAT_SCHEDULE = {
    'crawl-songs-every-minutes': {
        'task': "crawl_songs",    
        # 'schedule': crontab(minute=0, hour=f'*/{CRAWL_INTERVAL_TIME}'),  # Every 3 hours
        'schedule': crontab(minute='*/5'),  # Every minute
        'args': (),  # Pass any arguments to the task here
    },
}
# Initialize Celery with Redis as the broker
def create_celery_app(module):
    celery = Celery(module,broker=REDIS_URL,include=CELERY_TASK_LIST)
    
    celery.conf.beat_schedule = CELERY_BEAT_SCHEDULE
    celery.conf.timezone = 'UTC'
    
    # class TaskBase(celery.Task):
    #     max_retries = None # set to None to infinite retries
    #     retry_kwargs = {}

    #     def __init__(self, *args, **kwargs):
    #         super().__init__(*args, **kwargs)
    #         self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    #         if not hasattr(self, '_orig_run'):
    #             @wraps(self.run)
    #             def run(*args, **kwargs):
    #                 try:
    #                     self._logger.info(f"Running task: {self.name}")
    #                     return self._orig_run(*args, **kwargs)
    #                 # Add retry to all task in this worker if catch any exception
    #                 # and log the error before retry
    #                 except Exception as exc:
    #                     self._logger.exception(f"Task {self.name} encountered an error and will retry: {exc}")

    #                     if 'countdown' not in self.retry_kwargs:
    #                         retry_kwargs = self.retry_kwargs.copy()
    #                         retry_kwargs.update({'countdown': DEFAULT_INTERVAL_TIME_IN_SECOND})
    #                     else:
    #                         retry_kwargs = self.retry_kwargs

    #                     raise self.retry(**retry_kwargs)

    #             self._orig_run, self.run = self.run, run

    # celery.Task = TaskBase
    return celery

app = create_celery_app('crawl_worker')
logger.info("Celery worker initialized.")