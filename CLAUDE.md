# LoRA Cloud - Project Status for AI Assistants

## Project Overview
A web application for training LoRAs on cloud GPUs (vast.ai) and using them in ComfyUI for image generation.

## Current State

### ✅ Completed
1. **SSH Authentication Fixed**
   - Fixed the "q must be exactly 160, 224, or 256 bits long" error
   - SSH now uses pre-loaded PKey objects instead of file paths
   - Added `allow_agent=False` and `look_for_keys=False` to prevent scanning encrypted keys
   - SSHTunnelForwarder now receives PKey objects, not paths
   - Added path expansion (`~` to full path) for SSH key paths
   - Added fallback to default key when custom path doesn't exist

2. **SSH Key Configuration**
   - Working key: `~/.ssh/vast_rsa` (RSA, unencrypted)
   - This key is registered with vast.ai account
   - SSH connections now work: `ssh -i ~/.ssh/vast_rsa -p 11450 root@ssh3.vast.ai`

3. **LoRA Upload to GCS**
   - Training now uploads completed LoRAs to GCS after training
   - Uses base64 encoding to transfer files over SSH
   - Uploads to `loras/{lora_name}.safetensors` in GCS bucket

4. **ComfyUI Integration Endpoints**
   - `POST /api/loras/sync-to-comfyui` - Syncs LoRAs to ComfyUI
   - `GET /api/loras/{name}/comfyui-loader` - Gets ComfyUI node config

5. **Logging**
   - Comprehensive logging added to `training.py` and `ssh.py`
   - Shows SSH connection details, training progress, and errors

### ❌ Current Blockers

1. **Vast.ai Instance GPU Issue**
   - Current instance has CUDA/PyTorch mismatch
   - `torch.cuda.is_available()` returns `False` despite GPU being present
   - nvidia-smi shows RTX 4090 with errors
   - ComfyUI cannot start because it requires GPU
   - **Solution needed**: Destroy current instance and create new one with proper ComfyUI image

2. **Cannot Access .env File**
   - macOS permission error: `PermissionError: [Errno 1] Operation not permitted: '.env'`
   - This blocks programmatic API calls to vast.ai
   - Workaround: User needs to run commands manually or via vast.ai web UI

3. **Git Push Failing**
   - Credential issues preventing git push
   - User needs to push manually: `git push origin main`

### 🔄 Pending Tasks

1. **Deploy ComfyUI Instance**
   - Destroy current broken instance
   - Create new instance with image: `ghcr.io/ai-dock/comfyui:latest` or similar
   - Or use a vast.ai template with ComfyUI pre-installed
   - Verify GPU works: `python -c "import torch; print(torch.cuda.is_available())"`

2. **LoRA Tab Not Showing LoRAs**
   - The training simulation creates dummy files
   - Need to verify GCS upload is working
   - Check if `gcs_service.list_loras()` returns the uploaded files

3. **ComfyUI Tunnel**
   - Once ComfyUI is running on instance (port 8188)
   - Create tunnel: `POST /api/instances/{id}/tunnel` with `remote_port: 8188`
   - Access at `http://localhost:8188`

## Key Files

- `ui/backend/services/ssh.py` - SSH connections and tunnels
- `ui/backend/services/vast.py` - Vast.ai API integration
- `ui/backend/api/training.py` - Training job management
- `ui/backend/api/loras.py` - LoRA management and ComfyUI endpoints
- `ui/backend/api/instances.py` - Instance management
- `docker/comfyui/` - ComfyUI Docker configuration

## Commands for Next Steps

```bash
# 1. Push the committed changes (run manually)
git push origin main

# 2. Get vast.ai API key
grep VAST_API_KEY ui/backend/.env

# 3. Destroy current instance via vast.ai CLI or web UI
# Go to https://cloud.vast.ai/instances/ and delete the instance

# 4. Create new instance with ComfyUI
# Use vastai CLI or web UI to rent with image: ghcr.io/ai-dock/comfyui:latest

# 5. Verify ComfyUI is running
ssh -i ~/.ssh/vast_rsa -p <port> root@<host> "curl -s localhost:8188"

# 6. Create tunnel
curl -X POST http://localhost:8000/api/instances/<id>/tunnel \
  -H "Content-Type: application/json" \
  -d '{"remote_port": 8188, "local_port": 8188}'
```

## Environment
- macOS
- Python 3.11
- Backend: FastAPI on port 8000
- SSH keys in `~/.ssh/` (vast_rsa is the working unencrypted key)
