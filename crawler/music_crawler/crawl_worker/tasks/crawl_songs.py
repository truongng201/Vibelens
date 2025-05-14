# tasks.py
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from music_crawler.spiders.songs import SongsSpider
from ..main import app

@app.task(name="crawl_songs")
def crawl_songs():
    print(f"Starting crawling songs...")
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(SongsSpider)
    process.start()
    return f"Crawling completed"