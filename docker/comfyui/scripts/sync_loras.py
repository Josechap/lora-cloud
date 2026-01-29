#!/usr/bin/env python3
import os
from google.cloud import storage

BUCKET = os.environ.get("GCS_BUCKET")
LORA_DIR = "/workspace/ComfyUI/models/loras"

def sync_loras():
    os.makedirs(LORA_DIR, exist_ok=True)

    client = storage.Client()
    bucket = client.bucket(BUCKET)

    for blob in bucket.list_blobs(prefix="loras/"):
        if blob.name.endswith(".safetensors"):
            local_path = os.path.join(LORA_DIR, blob.name.split("/")[-1])
            if not os.path.exists(local_path):
                blob.download_to_filename(local_path)
                print(f"Downloaded: {blob.name}")

if __name__ == "__main__":
    sync_loras()
