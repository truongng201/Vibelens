from ..main import app
import subprocess
import logging
from crawl_worker.utils.Cache import Cache
import os
import threading

logger = logging.getLogger(__name__)

@app.task(name="crawl_songs_hopamchuan")
def crawl_songs_hopamchuan():
    print("Start crawling ...")

    SEED_URL = "https://hopamchuan.com/rhythm/v"
    START_INFO = [
        {"rhythm": "ballad", "max_offset": 30000},
        {"rhythm": "blue", "max_offset": 5000},
        {"rhythm": "disco", "max_offset": 2000},
        {"rhythm": "slow", "max_offset": 2000},
        {"rhythm": "rock", "max_offset": 2000},
        {"rhythm": "valse", "max_offset": 1000},
        {"rhythm": "fox", "max_offset": 1000},
        {"rhythm": "pop", "max_offset": 1000},
    ]

    try:
        # Determine next rhythm + offset to crawl
        rhythm = ""
        start_offset = 0
        max_offset = 10

        for item in START_INFO:
            rhythm = item.get("rhythm")
            url = f"{SEED_URL}/{rhythm}"
            max_offset = item.get("max_offset", 1000)
            curr_offset = int(Cache().get(url) or 0)

            if curr_offset + 10 < max_offset:
                start_offset = curr_offset + 10
                break  # Found next rhythm to crawl
            else:
                url = None
                rhythm = None
                start_offset = 0
                max_offset = 0
                continue
        
        # If all rhythms are done, reset the cache
        if url is None or rhythm is None:
            return "All rhythms are done"

        # Build scrapy command
        cmd = [
            "scrapy", "crawl", "hopamchuan", "-L", "DEBUG",
            "-a", f"url={url}",
            "-a", f"rhythm={rhythm}",
            "-a", f"start_offset={start_offset}",
            "-a", f"max_offset={max_offset}"
        ]

        # Debug: Print command
        logger.info("Running command: " + " ".join(cmd))
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        # Run spider process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,  # line-buffered
            universal_newlines=True,
            env=env
        )

        # Read both stdout and stderr without blocking

        def log_stream(stream, log_fn):
            for line in iter(stream.readline, ''):
                log_fn(line.strip())

        stdout_thread = threading.Thread(target=log_stream, args=(process.stdout, logger.info))
        stderr_thread = threading.Thread(target=log_stream, args=(process.stderr, logger.debug))

        stdout_thread.start()
        stderr_thread.start()

        process.wait()
        stdout_thread.join()
        stderr_thread.join()

        logger.info(f"Scrapy exited with code {process.returncode}")

    except Exception as e:
        logger.error(f"Something went wrong during crawling: {e}")
        return "Crawling failed"

    return "Crawling completed"
