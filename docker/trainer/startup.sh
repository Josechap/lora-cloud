#!/bin/bash
set -e

echo "Syncing from GCS..."
python3 /workspace/scripts/sync_gcs.py pull

echo "Ready for training"
tail -f /dev/null
