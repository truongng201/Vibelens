# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from uuid import uuid4
import time

class UploadToVectorDatabasePipeline:
    def open_spider(self, spider):
        # Qdrant connection (adjust host/port or use API key if needed)
        qdrant_host = os.getenv("VECTOR_DATABASE_HOST", "localhost")
        qdrant_port = int(os.getenv("VECTOR_DATABASE_PORT", 6333))
        
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = os.getenv("VECTOR_DATABASE_COLLECTION_NAME", "default-collection")

        self.batch = []
        self.batch_size = 96  # Adjust batch size if needed

    def close_spider(self, spider):
        # Upload any remaining items in batch
        if self.batch:
            self.upload_batch()

    def process_item(self, item, spider):
        print("Vector database", item)
        try:
        # Prepare payload
            content = f"{item['title']} by {item['artist']}. Genre: {item['genre']}.\nLyrics:\n{item['lyrics']}"

            point = PointStruct(
                id=str(item.get('id', uuid4())),  # ID
                vector=item.get('vector', []),    # Expect vector field already in item
                payload={
                    "text": content,
                    "category": item.get('genre', 'unknown')
                }
            )

            self.batch.append(point)

            if len(self.batch) >= self.batch_size:
                self.upload_batch()

            return item
        except Exception as e:
            print(f"Error processing item {item['id']}: {e}")
            # Handle the error as needed (e.g., log it, skip the item, etc.)
            return None
        
    

    def upload_batch(self):
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=self.batch
            )
            print(f"✅ Upserted {len(self.batch)} points to Qdrant.")
            self.batch = []
        except Exception as e:
            print(f"❌ Error uploading batch: {e}")
            print("⏳ Waiting 60 seconds before retrying...")
            time.sleep(60)
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=self.batch
                )
                print(f"✅ Retried and uploaded {len(self.batch)} points.")
                self.batch = []
            except Exception as e2:
                print(f"❌ Failed again after retry: {e2}")
