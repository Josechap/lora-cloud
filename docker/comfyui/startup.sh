#!/bin/bash
set -e

echo "Syncing LoRAs from GCS..."
python3 /workspace/scripts/sync_loras.py

echo "Starting ComfyUI..."
cd /workspace/ComfyUI
python3 main.py --listen 0.0.0.0 --port 8188
