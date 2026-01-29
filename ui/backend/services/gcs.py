from google.cloud import storage
from config import settings
from datetime import timedelta
import os

class GCSService:
    def __init__(self):
        self._client = None
        self._bucket = None

    @property
    def client(self):
        if self._client is None:
            self._client = storage.Client.from_service_account_json(
                settings.gcs_credentials_path
            )
        return self._client

    @property
    def bucket(self):
        if self._bucket is None:
            self._bucket = self.client.bucket(settings.gcs_bucket)
        return self._bucket

    def list_datasets(self) -> list[dict]:
        """List all datasets in the datasets/ prefix."""
        blobs = self.bucket.list_blobs(prefix="datasets/", delimiter="/")
        # Must consume iterator before accessing prefixes
        list(blobs)
        datasets = []
        for prefix in blobs.prefixes:
            name = prefix.replace("datasets/", "").rstrip("/")
            # Count files in dataset
            dataset_blobs = list(self.bucket.list_blobs(prefix=prefix))
            file_count = len(dataset_blobs)
            total_size = sum(b.size for b in dataset_blobs)
            datasets.append({
                "name": name,
                "path": prefix,
                "file_count": file_count,
                "total_size": total_size
            })
        return datasets

    def list_loras(self) -> list[dict]:
        """List all LoRAs in the loras/ prefix."""
        blobs = self.bucket.list_blobs(prefix="loras/")
        loras = []
        for blob in blobs:
            if blob.name.endswith(".safetensors"):
                loras.append({
                    "name": blob.name.split("/")[-1],
                    "path": blob.name,
                    "size": blob.size,
                    "updated": blob.updated.isoformat()
                })
        return loras

    def upload_file(self, local_path: str, remote_path: str):
        """Upload a file to GCS."""
        blob = self.bucket.blob(remote_path)
        blob.upload_from_filename(local_path)

    def download_file(self, remote_path: str, local_path: str):
        """Download a file from GCS."""
        blob = self.bucket.blob(remote_path)
        blob.download_to_filename(local_path)

    def delete_file(self, remote_path: str):
        """Delete a file from GCS."""
        blob = self.bucket.blob(remote_path)
        blob.delete()

    def get_dataset_files(self, name: str) -> list[dict]:
        """Get all files in a dataset."""
        blobs = self.bucket.list_blobs(prefix=f"datasets/{name}/")
        files = []
        for blob in blobs:
            files.append({
                "name": blob.name.split("/")[-1],
                "path": blob.name,
                "size": blob.size,
                "updated": blob.updated.isoformat() if blob.updated else None
            })
        return files

    def get_signed_url(self, remote_path: str, expiration_minutes: int = 60) -> str:
        """Generate a signed URL for downloading a file."""
        blob = self.bucket.blob(remote_path)
        return blob.generate_signed_url(
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )

    def get_upload_signed_url(self, remote_path: str, expiration_minutes: int = 60) -> str:
        """Generate a signed URL for uploading a file."""
        blob = self.bucket.blob(remote_path)
        return blob.generate_signed_url(
            expiration=timedelta(minutes=expiration_minutes),
            method="PUT",
            content_type="application/octet-stream"
        )

gcs_service = GCSService()
