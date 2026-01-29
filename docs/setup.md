# LoRA Cloud Setup Guide

## Prerequisites

- Docker installed locally
- vast.ai account with API key
- Google Cloud account with a GCS bucket

## 1. Google Cloud Storage Setup

1. Create a new GCS bucket (e.g., `my-lora-cloud`)
2. Create a service account with Storage Admin role
3. Download JSON credentials
4. Create folder structure:
   - `datasets/`
   - `loras/`
   - `models/`
   - `workflows/`

## 2. vast.ai Setup

1. Go to https://vast.ai/console/account
2. Copy your API key
3. Add SSH public key to your account

## 3. Local Configuration

1. Copy `.env.example` to `.env`
2. Fill in:
   ```
   VAST_API_KEY=your_key
   GCS_BUCKET=your_bucket
   GCS_CREDENTIALS_PATH=/path/to/creds.json
   ```

## 4. Build Docker Images

```bash
cd docker/trainer
docker build -t your-dockerhub/flux-lora-trainer .
docker push your-dockerhub/flux-lora-trainer

cd ../comfyui
docker build -t your-dockerhub/flux-comfyui .
docker push your-dockerhub/flux-comfyui
```

## 5. Start Local UI

```bash
docker-compose up
```

Open http://localhost:3000
