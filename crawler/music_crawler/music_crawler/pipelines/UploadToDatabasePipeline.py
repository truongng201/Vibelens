# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import psycopg2
import os
# from music_crawler.utils.KafkaProducer import KafkaProducer

class UploadToDatabasePipeline:
    def open_spider(self, spider):
        self.connection = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'vibelens'),
            user=os.getenv('POSTGRES_USER', 'admin'),
            password=os.getenv('POSTGRES_PASSWORD', 'admin')
        )
        self.cursor = self.connection.cursor()

    def close_spider(self, spider):
        # Commit any remaining transactions and close the connection
        if self.connection:
            self.connection.commit()
            # Close the cursor and connection
            self.cursor.close()
            self.connection.close()
            print("PostgreSQL connection closed.")

    def process_item(self, item, spider):
        # Check if the item already exists in the database
        try:
            self.cursor.execute("SELECT id FROM songs WHERE id = %s", (item['id'],))
            result = self.cursor.fetchone()
            if result: return None  # Skip if the item already exists
            # Insert the item into the database
            self.cursor.execute("""
                INSERT INTO songs (id, song_url, title, artist, genre, lyrics)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                item['id'],
                item['song_url'],
                item['title'],
                item['artist'],
                item['genre'],
                item['lyrics']
            ))
            # Commit the transaction
            self.connection.commit()
            print(f"Inserted item with ID {item['id']} into the database.")
            
            # Send the item to Kafka
            # kafka_producer = KafkaProducer(topic='crawl-song')
            # kafka_producer.send(item)
            # kafka_producer.flush()
            
        except psycopg2.Error as e:
            print(f"Error inserting item into the database: {e}")
            # Rollback in case of error
            self.connection.rollback()
            raise
        except Exception as e:
            print(f"Error processing item: {e}")
            # Rollback in case of error
            self.connection.rollback()
            raise
        return item