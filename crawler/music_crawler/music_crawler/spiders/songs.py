import scrapy
import time
import hashlib
import os
from music_crawler.items import SongItem


class SongsSpider(scrapy.Spider):
    name = "songs"
    allowed_domains = ["hopamchuan.com"]
    max_items = int(os.getenv("MAX_ITEMS", 5000))
    item_scraped = 0
    START_URLS = [
        {"url": "https://hopamchuan.com/rhythm/v/ballad", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/disco", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/blue", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/slow", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/rock", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/bolero", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/valse", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/fox", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/pop", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/boston", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/rock", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/bostonnova", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/chachacha", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/rhumba", "max_offset": 100000},
        {"url": "https://hopamchuan.com/rhythm/v/tango", "max_offset": 100000},
    ]

    def start_requests(self):   
        for start_url in self.START_URLS:
            url = start_url["url"]
            max_offset = start_url["max_offset"]
            for offset in range(0, max_offset, 10):
                # Stop generating requests if max_items is reached
                if self.item_scraped >= self.max_items:
                    print(f"[STOP] Reached max_items limit: {self.max_items}")
                    return
                yield scrapy.Request(url=f"{url}?offset={offset}", callback=self.parse_song_link)

    def parse_song_link(self, response):
        # Extract song links from the response
        song_links = response.css("a.song-title::attr(href)").getall()
        print(f"Found {len(song_links)} song links on {response.url}")

        for link in song_links:
            if self.item_scraped >= self.max_items:
                print(f"[STOP] Reached max_items limit during link parsing: {self.max_items}")
                return
            yield response.follow(link, callback=self.parse_song_metadata)

    def parse_song_metadata(self, response):
        if self.item_scraped >= self.max_items:
            print(f"[SKIP] Already reached max_items: {self.max_items}")
            return

        # Extract song metadata from the response
        title = response.css("#song-title span::text").get()
        artist = response.css(".author-item::text").get()
        genre = response.css("#display-rhythm::text").get() or "Unknown"
        lyrics = response.css(".hopamchuan_lyric *::text").getall()
        lyrics = "\n".join([line.strip() for line in lyrics if line.strip()])

        if not title or not artist or not lyrics:
            print(f"[WARN] Missing metadata for {response.url}")
            return

        # Clean up lyrics
        lyrics = lyrics.replace("\n", " ").replace("  ", " ").strip()

        # Generate unique ID
        song_id_hash = hashlib.md5(response.url.split("/")[-2].encode()).hexdigest()
        song_id = f"{song_id_hash}"

        self.item_scraped += 1
        print(f"[OK] Scraped {self.item_scraped}/{self.max_items}: {title} by {artist}")
        
        yield SongItem(
            id=song_id,
            song_url=response.url,
            title=title.strip(),
            artist=artist.strip(),
            genre=genre.strip(),
            lyrics=lyrics
        )
