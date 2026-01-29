from google.cloud import storage
from config import settings
import os

class GCSService:
    def __init__(self):
        self.client = storage.Client.from_service_account_json(
            settings.gcs_credentials_path
        )
        self.bucket = self.client.bucket(settings.gcs_bucket)

    def list_datasets(self) -> list[dict]:
        """List all datasets in the datasets/ prefix."""
        blobs = self.bucket.list_blobs(prefix="datasets/", delimiter="/")
        datasets = []
        for prefix in blobs.prefixes:
            name = prefix.replace("datasets/", "").rstrip("/")
            datasets.append({"name": name, "path": prefix})
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

gcs_service = GCSService()
