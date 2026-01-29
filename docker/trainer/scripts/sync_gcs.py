#!/usr/bin/env python3
"""Sync datasets and LoRAs with Google Cloud Storage."""
import os
import sys
from pathlib import Path

try:
    from google.cloud import storage
except ImportError:
    print("google-cloud-storage not installed, run: pip install google-cloud-storage")
    sys.exit(1)

BUCKET = os.environ.get("GCS_BUCKET")
WORKSPACE = Path("/workspace")

def get_client():
    """Get authenticated GCS client."""
    if not BUCKET:
        raise ValueError("GCS_BUCKET environment variable not set")
    return storage.Client()

def sync_pull(dataset_name=None):
    """Download datasets from GCS."""
    client = get_client()
    bucket = client.bucket(BUCKET)

    prefix = f"datasets/{dataset_name}/" if dataset_name else "datasets/"
    blobs = list(bucket.list_blobs(prefix=prefix))

    if not blobs:
        print(f"No files found in gs://{BUCKET}/{prefix}")
        return

    print(f"Downloading {len(blobs)} files from GCS...")
    for i, blob in enumerate(blobs, 1):
        local_path = WORKSPACE / blob.name
        local_path.parent.mkdir(parents=True, exist_ok=True)
        blob.download_to_filename(str(local_path))
        print(f"  [{i}/{len(blobs)}] {blob.name}")

    print(f"Done! Files saved to {WORKSPACE / 'datasets'}")

def sync_push():
    """Upload trained LoRAs to GCS."""
    client = get_client()
    bucket = client.bucket(BUCKET)

    output_dir = WORKSPACE / "output"
    if not output_dir.exists():
        print(f"No output directory found at {output_dir}")
        return

    safetensors = list(output_dir.glob("**/*.safetensors"))
    if not safetensors:
        print("No .safetensors files found to upload")
        return

    print(f"Uploading {len(safetensors)} LoRA files to GCS...")
    for i, local_path in enumerate(safetensors, 1):
        remote_path = f"loras/{local_path.name}"
        blob = bucket.blob(remote_path)
        blob.upload_from_filename(str(local_path))
        print(f"  [{i}/{len(safetensors)}] {remote_path}")

    print(f"Done! LoRAs uploaded to gs://{BUCKET}/loras/")

def show_help():
    print("""
GCS Sync Tool for LoRA Cloud

Usage:
    python sync_gcs.py pull [dataset_name]  - Download datasets
    python sync_gcs.py push                 - Upload trained LoRAs

Environment:
    GCS_BUCKET                       - GCS bucket name (required)
    GOOGLE_APPLICATION_CREDENTIALS   - Path to service account JSON
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    cmd = sys.argv[1]
    try:
        if cmd == "pull":
            dataset = sys.argv[2] if len(sys.argv) > 2 else None
            sync_pull(dataset)
        elif cmd == "push":
            sync_push()
        elif cmd in ("-h", "--help", "help"):
            show_help()
        else:
            print(f"Unknown command: {cmd}")
            show_help()
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
