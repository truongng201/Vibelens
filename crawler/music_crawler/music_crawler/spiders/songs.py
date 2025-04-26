import random
import string
import hashlib
import os
import time
import itertools
from music_crawler.items import SongItem
from scrapy_selenium import SeleniumRequest
from scrapy import Spider
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException

class SongsSpider(Spider):
    name = "songs"
    allowed_domains = ["azlyrics.com"]
    max_items = int(os.getenv("MAX_ITEMS", 10))
    item_scraped = 0

    # List of user agents for rotation
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"
    ]

    start_urls = [f"https://www.azlyrics.com/{letter}.html" for letter in string.ascii_lowercase]
    start_urls.append("https://www.azlyrics.com/19.html")

    def rotate_ua(self):
        """Return an iterator for cycling through user agents."""
        return itertools.cycle(self.user_agents)
    
    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"Scraping {url}")
            yield SeleniumRequest(
                url=url,
                callback=self.get_artists_url,
                wait_time=2,  # Increased wait time for stability
                meta={
                    'selenium_options': self.get_selenium_options()
                }
            )

    def get_selenium_options(self):
        """Configure Selenium options with rotated user agent and headless mode."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        ua_iterator = self.rotate_ua()
        chrome_options.add_argument(f"user-agent={next(ua_iterator)}")
        return chrome_options

    def get_artists_url(self, response):
        try:
            driver = response.meta['driver']
            artist_links = driver.find_elements(By.CSS_SELECTOR, "div.col-sm-6.text-center.artist-col a")
            self.logger.info(f"Found {len(artist_links)} artist links on {response.url}")
            
            for a in artist_links:
                href = a.get_attribute("href")
                yield SeleniumRequest(
                    url=href,
                    callback=self.get_songs_url,
                    wait_time=2,
                    meta={
                        'selenium_options': self.get_selenium_options()
                    }
                )
        except (TimeoutException, WebDriverException) as e:
            self.logger.error(f"Error fetching artist links from {response.url}: {str(e)}")

    def get_songs_url(self, response):
        try:
            driver = response.meta['driver']
            song_links = driver.find_elements(By.CSS_SELECTOR, ".listalbum-item a")
            for a in song_links:
                
                href = a.get_attribute("href")
                yield SeleniumRequest(
                    url=href,
                    callback=self.parse_song_metadata,
                    wait_time=2,
                    meta={
                        'selenium_options': self.get_selenium_options()
                    }
                )
        except (TimeoutException, WebDriverException) as e:
            self.logger.error(f"Error fetching song links from {response.url}: {str(e)}")

    def parse_song_metadata(self, response):
        if self.item_scraped >= self.max_items:
            self.logger.info(f"Reached max items limit: {self.max_items}")
            return

        try:
            driver = response.meta['driver']
            b_tags = driver.find_elements(By.TAG_NAME, "b")

            if len(b_tags) < 2:
                self.logger.warning(f"Missing artist or title on {response.url}")
                return

            artist = b_tags[0].text.strip().replace(" Lyrics", "")
            title = b_tags[1].text.strip().replace('"', "")

            lyrics_divs = driver.find_elements(By.XPATH, "//div[not(@class) and not(@id)]")
            
            # Get the div with the most text
            longest_div = max(lyrics_divs, key=lambda div: len(div.text.strip()))

            # Extract the text
            lyrics = longest_div.text.strip()

            if not title or not artist or not lyrics:
                self.logger.warning(f"Missing metadata for {response.url}")
                return

            lyrics = lyrics.replace('" ', " ").replace("\n", " ").replace('"', "").strip()

            song_id_hash = hashlib.md5(response.url.split("/")[-2].encode()).hexdigest()
            song_id = f"{song_id_hash}"
            self.item_scraped += 1
            self.logger.info(f"Scraped song: {title} by {artist}")

            yield SongItem(
                id=song_id,
                song_url=response.url,
                title=title,
                artist=artist,
                lyrics=lyrics
            )
        except (TimeoutException, WebDriverException) as e:
            self.logger.error(f"Error parsing song metadata from {response.url}: {str(e)}")