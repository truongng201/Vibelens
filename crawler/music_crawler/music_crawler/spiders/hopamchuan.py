import scrapy
import hashlib
import os
from music_crawler.items import SongItem
from music_crawler.utils.Cache import Cache 
from scrapy.exceptions import CloseSpider

MAX_SONG_ITEM = int(os.getenv("MAX_SONG_ITEM", 1000))

class HopAmChuanSpider(scrapy.Spider):
    name = "hopamchuan"
    allowed_domains = ["hopamchuan.com"]

    def __init__(self, url=None, rhythm=None, start_offset=0, max_offset=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.rhythm = rhythm
        self.current_offset = int(start_offset)
        self.max_offset = int(max_offset)
        self.songs_scraped = 0
        print(f"[Start crawling] Rhythm: {self.rhythm} | URL: {self.url} | Offset: {self.current_offset} → {self.max_offset}")

    def start_requests(self):
        yield scrapy.Request(
            url=f"{self.url}?offset={self.current_offset}",
            callback=self.parse_song_link,
            cb_kwargs={"offset": self.current_offset}
        )

    def parse_song_link(self, response, offset):
        try:
            song_links = response.css("a.song-title::attr(href)").getall()
            print(f"[{self.rhythm}] Found {len(song_links)} song links on offset {offset}: {response.url}")

            # Save last offset to cache
            Cache().set(self.url, offset)

            for link in song_links:
                # Stop yielding more song detail requests if max reached
                if self.songs_scraped >= MAX_SONG_ITEM:
                    raise CloseSpider(f"Reached max songs limit: {MAX_SONG_ITEM}")
                yield response.follow(link, callback=self.parse_song_metadata)

            # After processing current page, request next page if limit not reached
            if self.songs_scraped < MAX_SONG_ITEM:
                next_offset = offset + 10
                if next_offset <= self.max_offset:
                    yield scrapy.Request(
                        url=f"{self.url}?offset={next_offset}",
                        callback=self.parse_song_link,
                        cb_kwargs={"offset": next_offset}
                    )
                else:
                    print("[INFO] Reached max offset limit, stopping crawl.")

        except CloseSpider:
            raise
        except Exception as e:
            print(f"[ERROR] Failed to parse song links on {response.url}: {e}")

    def parse_song_metadata(self, response):
        try:
            title = response.css("#song-title span::text").get()
            artist = response.css(".author-item::text").get()
            genre = response.css("#display-rhythm::text").get() or "Unknown"
            lyrics = response.css(".hopamchuan_lyric *::text").getall()
            lyrics = "\n".join([line.strip() for line in lyrics if line.strip()])
            lyrics = lyrics.replace("\n", " ").replace("  ", " ").strip()

            
            song_id_hash = hashlib.md5(response.url.split("/")[-2].encode()).hexdigest()
            song_id = f"{song_id_hash}"

            print(f"[OK] Scraped: '{title}' by {artist}")

            self.songs_scraped += 1

            yield SongItem(
                id=song_id,
                song_url=response.url,
                title=title.strip(),
                artist=artist.strip(),
                genre=genre.strip(),
                lyrics=lyrics
            )
        except Exception as e:
            print(f"[ERROR] Failed to parse song metadata on {response.url}: {e}")
