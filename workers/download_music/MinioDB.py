from minio import Minio
from minio.error import S3Error
import os

class MinioDB:
    def __init__(self):
        self.endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.secure = False
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "test")
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )

    def upload_mp3(self, file_path: str, object_name: str = None):
        try:
            # Ensure bucket exists
            if not self.client.bucket_exists(self.bucket_name):
                raise Exception(f"Bucket {self.bucket_name} not exist")

            # Use filename if object_name not provided
            if object_name is None:
                object_name = os.path.basename(file_path)

            # Upload the file
            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=file_path,
                content_type="audio/mpeg"
            )
            print(f"📤 Uploaded '{file_path}' to bucket '{self.bucket_name}' as '{object_name}'.")

        except S3Error as e:
            print(f"❌ MinIO Error: {e}")
        except Exception as e:
            print(f"❌ Upload Error: {e}")
