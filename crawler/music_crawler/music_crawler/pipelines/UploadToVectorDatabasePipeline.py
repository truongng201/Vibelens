# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import os
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from music_crawler.utils.model_loader import _model_instance, get_model
from uuid import uuid4

class UploadToVectorDatabasePipeline:
    def open_spider(self, spider):
        # Qdrant connection (adjust host/port or use API key if needed)
        qdrant_host = os.getenv("VECTOR_DATABASE_HOST", "localhost")
        qdrant_port = int(os.getenv("VECTOR_DATABASE_PORT", 6333))
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = os.getenv("VECTOR_DATABASE_COLLECTION_NAME", "default_collection")
        self.vector_name = os.getenv("VECTOR_DATABASE_VECTOR_NAME", "default_vector")
        # Load the model
        # Ensure the model is loaded only once
        global _model_instance
        if _model_instance is None:
            print("🔵 Loading the model...")
            _model_instance = get_model()
        else:
            print("✅ Model already loaded.")
        # Initialize the model
        self.model = _model_instance
        self.batch = []
        self.batch_size = 10  # Adjust batch size if needed
        try:
            self.client.get_collection(collection_name=self.collection_name)
        except Exception:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config={
                    self.vector_name: VectorParams(
                        size=384,                  # ⚡ Adjust depending on your model
                        distance=Distance.COSINE   # or .DOT, .EUCLID if you want
                    )
                },
            )
            print(f"✅ Created collection '{self.collection_name}' with vector name '{self.vector_name}'.")

    def close_spider(self, spider):
        # Upload any remaining items in batch
        if self.batch:
            self.upload_batch()

    def process_item(self, item, spider):
        try:
            # Prepare payload
            content = f"{item['title']} by {item['artist']}. Genre: {item['genre']}.\nLyrics:\n{item['lyrics']}"
            print(f"🔵 Processing item {item['id']}... ")
            # Generate vector using the model
            vector = self.model.encode(content).tolist()  # Convert to list for Qdrant
            point = PointStruct(
                id=str(item.get('id', uuid4())),  # ID
                vector={  # <--- This must be a dict now
                    self.vector_name: vector
                },  # Vector
                payload={
                    "text": content,
                    "category": item.get('genre', 'unknown')
                }
            )

            self.batch.append(point)
            print(f"🔵 Added item {item['id']} to batch. Batch size: {len(self.batch)}")
            if len(self.batch) >= self.batch_size:
                self.upload_batch()

        except Exception as e:
            print(f"Error processing item {item['id']}: {e}")
        return item
    
    def upload_batch(self):
        try:
            print(f"Uploading batch of {len(self.batch)} points to Qdrant...")
            self.client.upsert(
                collection_name=self.collection_name,
                wait=True,
                points=self.batch
            )
            print(f"✅ Upserted {len(self.batch)} points to Qdrant.")
            self.batch = []
        except Exception as e:
            print(f"Error uploading batch to Qdrant: {e}")
