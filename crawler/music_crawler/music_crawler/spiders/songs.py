import scrapy
import time
import hashlib
import os
from music_crawler.items import SongItem


class SongsSpider(scrapy.Spider):
    name = "songs"
    allowed_domains = ["hopamchuan.com"]
    max_items = int(os.getenv("MAX_ITEMS", 1000))
    item_scraped = 0
    START_URLS = [
        {"url": "https://hopamchuan.com/rhythm/v/ballad", "max_offset": 10000},
        {"url": "https://hopamchuan.com/rhythm/v/disco", "max_offset": 10000},
        {"url": "https://hopamchuan.com/rhythm/v/blue", "max_offset": 10000},
        {"url": "https://hopamchuan.com/rhythm/v/slow", "max_offset": 10000},
        {"url": "https://hopamchuan.com/rhythm/v/rock", "max_offset": 10000},
    ]
    
    def start_requests(self):   
        for start_url in self.START_URLS:
            url = start_url["url"]
            max_offset = start_url["max_offset"]
            for offset in range(0, max_offset, 10):
                yield scrapy.Request(url=f"{url}?offset={offset}", callback=self.parse_song_link)
        
    def parse_song_link(self, response):
        # Extract song links from the response
        song_links = response.css("a.song-title::attr(href)").getall()
        print(f"Found {len(song_links)} song links on {response.url}")
        for link in song_links:
            yield response.follow(link, callback=self.parse_song_metadata)
    
    def parse_song_metadata(self, response):
        if self.max_items and self.item_scraped >= self.max_items:
            print(f"Reached max items limit: {self.max_items}")
            return
        
        # Extract song metadata from the response
        title = response.css("#song-title span::text").get()
        artist = response.css(".author-item::text").get()
        genre = response.css("#display-rhythm::text").get() or "Unknown"
        lyrics = response.css(".hopamchuan_lyric *::text").getall()
        lyrics = "\n".join([line.strip() for line in lyrics if line.strip()])
        
        if not title or not artist or not lyrics:
            print(f"Missing metadata for {response.url}")
            return
        
        # Clean up the lyrics text
        lyrics = lyrics.replace("\n", " ").replace("  ", " ").strip()
        
        # Generate a unique ID for the song
        song_id_hash = hashlib.md5(response.url.split("/")[-2].encode()).hexdigest()
        song_id = f"{song_id_hash}"
        self.item_scraped += 1
        print(f"Scraped song: {title} by {artist}")
        yield SongItem(
            id = song_id,
            song_url=response.url,
            title=title.strip(),
            artist=artist.strip(),
            genre=genre.strip(),
            lyrics=lyrics
        )
        