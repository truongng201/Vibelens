# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class SongItem(scrapy.Item):
    id = scrapy.Field()
    song_url = scrapy.Field()
    title = scrapy.Field()
    artist = scrapy.Field()
    genre = scrapy.Field()
    lyrics = scrapy.Field()


