#!/usr/bin/env python3
import os
import sys
from google.cloud import storage

BUCKET = os.environ.get("GCS_BUCKET")

def sync_pull():
    client = storage.Client()
    bucket = client.bucket(BUCKET)

    # Pull datasets
    for blob in bucket.list_blobs(prefix="datasets/"):
        local_path = f"/workspace/{blob.name}"
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)
        print(f"Downloaded {blob.name}")

def sync_push():
    client = storage.Client()
    bucket = client.bucket(BUCKET)

    # Push outputs
    for root, dirs, files in os.walk("/workspace/outputs"):
        for f in files:
            if f.endswith(".safetensors"):
                local_path = os.path.join(root, f)
                remote_path = f"loras/{f}"
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(local_path)
                print(f"Uploaded {remote_path}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pull"
    if cmd == "pull":
        sync_pull()
    elif cmd == "push":
        sync_push()
