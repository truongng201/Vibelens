from minio import Minio
from minio.error import S3Error
import os
from datetime import timedelta

class MinioDB:
    def __init__(self):
        self.endpoint_internal = os.getenv('MINIO_INTERNAL', 'minio:9000')
        self.endpoint_external = os.getenv('MINIO_EXTERNAL', 'localhost:9000')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.secure_internal = os.getenv('MINIO_SECURE_INTERNAL', 'false').lower() in ['true', '1', 'yes']
        self.secure_external = os.getenv('MINIO_SECURE_EXTERNAL', 'false').lower() in ['true', '1', 'yes']

        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "test")

        self.client = Minio(
            self.endpoint_internal,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure_internal
        )
        
        self.presigned_client = Minio(
            self.endpoint_external,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure_external
        )

    def upload_mp3(self, file_path: str, object_name: str = None, extension: str = "mp3"):
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
                object_name=object_name + f".{extension}",
                file_path=file_path,
                content_type=f"audio/{extension}"
            )
            print(f"📤 Uploaded '{file_path}' to bucket '{self.bucket_name}' as '{object_name}'.")


        except S3Error as e:
            print(f"❌ MinIO Error: {e}")
        except Exception as e:
            print(f"❌ Upload Error: {e}")

    def upload_image(self, file_path: str, object_name: str = None, extension: str = "jpg"):
        try:
            # Ensure bucket exists
            if not self.client.bucket_exists(self.bucket_name):
                raise Exception(f"Bucket {self.bucket_name} not exist")

            # Use filename if object_name not provided
            if object_name is None:
                object_name = os.path.basename(file_path)

            # Set content type for common image extensions
            content_type = f"image/{extension if extension != 'jpg' else 'jpeg'}"

            # Upload the image file
            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_name + f".{extension}",
                file_path=file_path,
                content_type=content_type
            )
            print(f"📤 Uploaded image '{file_path}' to bucket '{self.bucket_name}' as '{object_name}.{extension}'.")

        except S3Error as e:
            print(f"❌ MinIO Error: {e}")
        except Exception as e:
            print(f"❌ Upload Error: {e}")

    def get_presigned_url(self, object_name, expiry=timedelta(minutes=15)):
        return self.presigned_client.presigned_get_object(
            self.bucket_name, object_name, expires=expiry
        )