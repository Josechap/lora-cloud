#!/bin/bash
set -e

echo "========================================"
echo "  LoRA Cloud Trainer Container"
echo "========================================"

# Start SSH server if installed
if command -v sshd &> /dev/null; then
    echo "[*] Starting SSH server..."
    mkdir -p /run/sshd
    /usr/sbin/sshd
fi

# Sync datasets from GCS
if [ -n "$GCS_BUCKET" ] && [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "[*] Syncing datasets from GCS..."
    python3 /workspace/scripts/sync_gcs.py pull || echo "[!] GCS sync failed, continuing anyway"
else
    echo "[!] GCS not configured, skipping sync"
fi

echo ""
echo "========================================"
echo "  Container ready!"
echo "  - Datasets: /workspace/dataset/"
echo "  - Output:   /workspace/output/"
echo "  - Scripts:  /workspace/scripts/"
echo "========================================"
echo ""

# Keep container running
tail -f /dev/null
