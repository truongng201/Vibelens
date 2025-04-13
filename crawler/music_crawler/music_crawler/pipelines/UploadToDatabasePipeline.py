# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import psycopg2
import os

class UploadToDatabasePipeline:
    def open_spider(self, spider):
        self.connection = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'your_database_name'),
            user=os.getenv('POSTGRES_USER', 'your_username'),
            password=os.getenv('POSTGRES_PASSWORD', 'your_password')
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
        except psycopg2.Error as e:
            print(f"Error inserting item into the database: {e}")
            # Rollback in case of error
            self.connection.rollback()
            raise
        return item