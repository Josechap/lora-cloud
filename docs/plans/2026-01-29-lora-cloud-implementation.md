# LoRA Cloud Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a complete system for training Flux LoRAs on vast.ai with a local web UI for management.

**Architecture:** Two Docker images (trainer + ComfyUI) deployed to vast.ai, managed via local FastAPI backend with React frontend. GCS for persistent storage.

**Tech Stack:** Python 3.10, FastAPI, React, Tailwind, Docker, kohya_ss, ComfyUI, Google Cloud Storage

---

## Phase 1: Project Foundation

### Task 1: Initialize Project Structure

**Files:**
- Create: `requirements.txt`
- Create: `docker-compose.yml`
- Create: `.gitignore`
- Create: `README.md`

**Step 1: Create requirements.txt**

```txt
# Backend
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
websockets==12.0
httpx==0.26.0
python-dotenv==1.0.0

# vast.ai & cloud
google-cloud-storage==2.14.0
paramiko==3.4.0
sshtunnel==0.4.0

# Utils
pydantic==2.5.3
pydantic-settings==2.1.0
```

**Step 2: Create .gitignore**

```
__pycache__/
*.py[cod]
.env
.venv/
venv/
node_modules/
dist/
build/
*.egg-info/
.DS_Store
```

**Step 3: Create docker-compose.yml for local dev**

```yaml
version: '3.8'
services:
  backend:
    build: ./ui/backend
    ports:
      - "8000:8000"
    volumes:
      - ./ui/backend:/app
    env_file:
      - .env
```

**Step 4: Create README.md**

```markdown
# LoRA Cloud

Train Flux LoRAs on vast.ai with a local web UI.

## Quick Start

1. Copy `.env.example` to `.env` and fill in credentials
2. Run `docker-compose up`
3. Open http://localhost:3000

## Documentation

See `docs/` for setup guides.
```

**Step 5: Commit**

```bash
git add requirements.txt docker-compose.yml .gitignore README.md
git commit -m "feat: initialize project structure"
```

---

### Task 2: Backend Foundation - FastAPI Setup

**Files:**
- Create: `ui/backend/main.py`
- Create: `ui/backend/config.py`
- Create: `ui/backend/Dockerfile`
- Create: `.env.example`

**Step 1: Create config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    vast_api_key: str = ""
    gcs_bucket: str = ""
    gcs_credentials_path: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 2: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LoRA Cloud")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
```

**Step 3: Create Dockerfile**

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Step 4: Create .env.example**

```
VAST_API_KEY=your_vast_api_key
GCS_BUCKET=your_bucket_name
GCS_CREDENTIALS_PATH=/path/to/credentials.json
```

**Step 5: Commit**

```bash
git add ui/backend/ .env.example
git commit -m "feat: add FastAPI backend foundation"
```

---

### Task 3: GCS Service

**Files:**
- Create: `ui/backend/services/gcs.py`
- Create: `ui/backend/services/__init__.py`

**Step 1: Create __init__.py**

```python
# Services package
```

**Step 2: Create gcs.py**

```python
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
```

**Step 3: Commit**

```bash
git add ui/backend/services/
git commit -m "feat: add GCS service for cloud storage"
```

---

### Task 4: Vast.ai Service

**Files:**
- Create: `ui/backend/services/vast.py`

**Step 1: Create vast.py**

```python
import httpx
from config import settings
from typing import Optional

VAST_API_URL = "https://console.vast.ai/api/v0"

class VastService:
    def __init__(self):
        self.api_key = settings.vast_api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    async def search_gpus(
        self,
        gpu_name: str = "RTX 4090",
        min_gpu_ram: int = 24,
        max_price: float = 1.0
    ) -> list[dict]:
        """Search for available GPU instances."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{VAST_API_URL}/bundles",
                headers=self.headers,
                params={
                    "q": f"gpu_name={gpu_name} gpu_ram>={min_gpu_ram} dph<={max_price}"
                }
            )
            resp.raise_for_status()
            return resp.json().get("offers", [])

    async def rent_instance(
        self,
        offer_id: int,
        image: str,
        disk_gb: int = 50
    ) -> dict:
        """Rent a GPU instance."""
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{VAST_API_URL}/asks/{offer_id}/",
                headers=self.headers,
                json={
                    "client_id": "me",
                    "image": image,
                    "disk": disk_gb,
                    "onstart": "cd /workspace && ./startup.sh"
                }
            )
            resp.raise_for_status()
            return resp.json()

    async def get_instances(self) -> list[dict]:
        """Get all running instances."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{VAST_API_URL}/instances",
                headers=self.headers,
                params={"owner": "me"}
            )
            resp.raise_for_status()
            return resp.json().get("instances", [])

    async def get_instance(self, instance_id: int) -> Optional[dict]:
        """Get a specific instance."""
        instances = await self.get_instances()
        for inst in instances:
            if inst["id"] == instance_id:
                return inst
        return None

    async def destroy_instance(self, instance_id: int) -> bool:
        """Terminate an instance."""
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{VAST_API_URL}/instances/{instance_id}/",
                headers=self.headers
            )
            return resp.status_code == 200

vast_service = VastService()
```

**Step 2: Commit**

```bash
git add ui/backend/services/vast.py
git commit -m "feat: add vast.ai API service"
```

---

### Task 5: SSH Tunnel Service

**Files:**
- Create: `ui/backend/services/ssh.py`

**Step 1: Create ssh.py**

```python
from sshtunnel import SSHTunnelForwarder
import paramiko
from typing import Optional
import threading

class SSHService:
    def __init__(self):
        self.tunnels: dict[int, SSHTunnelForwarder] = {}
        self.lock = threading.Lock()

    def create_tunnel(
        self,
        instance_id: int,
        ssh_host: str,
        ssh_port: int,
        remote_port: int,
        local_port: int,
        ssh_key_path: str
    ) -> int:
        """Create SSH tunnel to instance, return local port."""
        with self.lock:
            if instance_id in self.tunnels:
                return self.tunnels[instance_id].local_bind_port

            tunnel = SSHTunnelForwarder(
                (ssh_host, ssh_port),
                ssh_username="root",
                ssh_pkey=ssh_key_path,
                remote_bind_address=("127.0.0.1", remote_port),
                local_bind_address=("127.0.0.1", local_port)
            )
            tunnel.start()
            self.tunnels[instance_id] = tunnel
            return tunnel.local_bind_port

    def close_tunnel(self, instance_id: int):
        """Close SSH tunnel for instance."""
        with self.lock:
            if instance_id in self.tunnels:
                self.tunnels[instance_id].stop()
                del self.tunnels[instance_id]

    def get_tunnel_port(self, instance_id: int) -> Optional[int]:
        """Get local port for existing tunnel."""
        with self.lock:
            if instance_id in self.tunnels:
                return self.tunnels[instance_id].local_bind_port
            return None

ssh_service = SSHService()
```

**Step 2: Commit**

```bash
git add ui/backend/services/ssh.py
git commit -m "feat: add SSH tunnel service"
```

---

## Phase 2: API Endpoints

### Task 6: Instances API

**Files:**
- Create: `ui/backend/api/__init__.py`
- Create: `ui/backend/api/instances.py`
- Modify: `ui/backend/main.py`

**Step 1: Create api/__init__.py**

```python
# API package
```

**Step 2: Create instances.py**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.vast import vast_service
from services.ssh import ssh_service
from typing import Optional

router = APIRouter(prefix="/instances", tags=["instances"])

class LaunchRequest(BaseModel):
    gpu_type: str = "RTX 4090"
    image: str
    disk_gb: int = 50
    max_price: float = 1.0

class TunnelRequest(BaseModel):
    remote_port: int
    local_port: int
    ssh_key_path: str

@router.get("")
async def list_instances():
    """List all running instances."""
    return await vast_service.get_instances()

@router.get("/{instance_id}")
async def get_instance(instance_id: int):
    """Get instance details."""
    instance = await vast_service.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, "Instance not found")
    return instance

@router.post("/launch")
async def launch_instance(req: LaunchRequest):
    """Find cheapest GPU and launch instance."""
    offers = await vast_service.search_gpus(
        gpu_name=req.gpu_type,
        max_price=req.max_price
    )
    if not offers:
        raise HTTPException(404, "No GPUs available at that price")

    # Pick cheapest
    offer = min(offers, key=lambda x: x.get("dph_total", 999))
    result = await vast_service.rent_instance(
        offer_id=offer["id"],
        image=req.image,
        disk_gb=req.disk_gb
    )
    return result

@router.delete("/{instance_id}")
async def destroy_instance(instance_id: int):
    """Terminate an instance."""
    ssh_service.close_tunnel(instance_id)
    success = await vast_service.destroy_instance(instance_id)
    if not success:
        raise HTTPException(500, "Failed to destroy instance")
    return {"status": "terminated"}

@router.post("/{instance_id}/tunnel")
async def create_tunnel(instance_id: int, req: TunnelRequest):
    """Create SSH tunnel to instance."""
    instance = await vast_service.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, "Instance not found")

    local_port = ssh_service.create_tunnel(
        instance_id=instance_id,
        ssh_host=instance["ssh_host"],
        ssh_port=instance["ssh_port"],
        remote_port=req.remote_port,
        local_port=req.local_port,
        ssh_key_path=req.ssh_key_path
    )
    return {"local_port": local_port}

@router.delete("/{instance_id}/tunnel")
async def close_tunnel(instance_id: int):
    """Close SSH tunnel."""
    ssh_service.close_tunnel(instance_id)
    return {"status": "closed"}
```

**Step 3: Update main.py to include router**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.instances import router as instances_router

app = FastAPI(title="LoRA Cloud")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(instances_router)

@app.get("/health")
def health():
    return {"status": "ok"}
```

**Step 4: Commit**

```bash
git add ui/backend/api/ ui/backend/main.py
git commit -m "feat: add instances API endpoints"
```

---

### Task 7: Datasets API

**Files:**
- Create: `ui/backend/api/datasets.py`
- Modify: `ui/backend/main.py`

**Step 1: Create datasets.py**

```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from services.gcs import gcs_service
import tempfile
import os

router = APIRouter(prefix="/datasets", tags=["datasets"])

@router.get("")
def list_datasets():
    """List all datasets."""
    return gcs_service.list_datasets()

@router.post("/{name}/upload")
async def upload_images(name: str, files: list[UploadFile] = File(...)):
    """Upload images to a dataset."""
    uploaded = []
    for file in files:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp.flush()

            remote_path = f"datasets/{name}/{file.filename}"
            gcs_service.upload_file(tmp.name, remote_path)
            uploaded.append(remote_path)
            os.unlink(tmp.name)

    return {"uploaded": uploaded}

@router.delete("/{name}")
def delete_dataset(name: str):
    """Delete a dataset."""
    blobs = gcs_service.bucket.list_blobs(prefix=f"datasets/{name}/")
    for blob in blobs:
        blob.delete()
    return {"status": "deleted"}
```

**Step 2: Add router to main.py**

Add import and include:
```python
from api.datasets import router as datasets_router
app.include_router(datasets_router)
```

**Step 3: Commit**

```bash
git add ui/backend/api/datasets.py ui/backend/main.py
git commit -m "feat: add datasets API endpoints"
```

---

### Task 8: LoRAs API

**Files:**
- Create: `ui/backend/api/loras.py`
- Modify: `ui/backend/main.py`

**Step 1: Create loras.py**

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from services.gcs import gcs_service
import tempfile

router = APIRouter(prefix="/loras", tags=["loras"])

@router.get("")
def list_loras():
    """List all trained LoRAs."""
    return gcs_service.list_loras()

@router.get("/{name}/download")
def download_lora(name: str):
    """Download a LoRA file."""
    loras = gcs_service.list_loras()
    lora = next((l for l in loras if l["name"] == name), None)
    if not lora:
        raise HTTPException(404, "LoRA not found")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".safetensors") as tmp:
        gcs_service.download_file(lora["path"], tmp.name)
        return FileResponse(tmp.name, filename=name)

@router.delete("/{name}")
def delete_lora(name: str):
    """Delete a LoRA."""
    loras = gcs_service.list_loras()
    lora = next((l for l in loras if l["name"] == name), None)
    if not lora:
        raise HTTPException(404, "LoRA not found")

    gcs_service.delete_file(lora["path"])
    return {"status": "deleted"}
```

**Step 2: Add router to main.py**

Add import and include:
```python
from api.loras import router as loras_router
app.include_router(loras_router)
```

**Step 3: Commit**

```bash
git add ui/backend/api/loras.py ui/backend/main.py
git commit -m "feat: add LoRAs API endpoints"
```

---

## Phase 3: Docker Images

### Task 9: Trainer Dockerfile

**Files:**
- Create: `docker/trainer/Dockerfile`
- Create: `docker/trainer/startup.sh`
- Create: `docker/trainer/requirements.txt`

**Step 1: Create docker/trainer/requirements.txt**

```txt
torch==2.1.2
torchvision==0.16.2
accelerate==0.25.0
transformers==4.36.2
diffusers==0.25.0
safetensors==0.4.1
google-cloud-storage==2.14.0
Pillow==10.2.0
opencv-python-headless==4.9.0.80
tqdm==4.66.1
toml==0.10.2
```

**Step 2: Create Dockerfile**

```dockerfile
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip git wget \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Python deps
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install kohya_ss
RUN git clone https://github.com/kohya-ss/sd-scripts.git /workspace/sd-scripts \
    && cd /workspace/sd-scripts \
    && pip3 install --no-cache-dir -r requirements.txt

# Install captioning models
RUN pip3 install --no-cache-dir \
    transformers[torch] \
    open-clip-torch

# Copy scripts and configs
COPY scripts/ /workspace/scripts/
COPY configs/ /workspace/configs/
COPY startup.sh /workspace/

RUN chmod +x /workspace/startup.sh

EXPOSE 22

CMD ["/workspace/startup.sh"]
```

**Step 3: Create startup.sh**

```bash
#!/bin/bash
set -e

echo "Syncing from GCS..."
python3 /workspace/scripts/sync_gcs.py pull

echo "Ready for training"
tail -f /dev/null
```

**Step 4: Commit**

```bash
git add docker/trainer/
git commit -m "feat: add trainer Docker image"
```

---

### Task 10: Trainer Scripts

**Files:**
- Create: `docker/trainer/scripts/sync_gcs.py`
- Create: `docker/trainer/scripts/prepare_dataset.py`
- Create: `docker/trainer/scripts/train_lora.py`

**Step 1: Create sync_gcs.py**

```python
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
```

**Step 2: Create prepare_dataset.py**

```python
#!/usr/bin/env python3
import argparse
import os
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
import torch

def caption_images(input_dir: str, model_name: str = "microsoft/Florence-2-base"):
    """Caption all images in directory using Florence-2."""
    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, torch_dtype=torch.float16
    ).cuda()

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue

        img_path = os.path.join(input_dir, fname)
        caption_path = os.path.splitext(img_path)[0] + ".txt"

        if os.path.exists(caption_path):
            continue

        image = Image.open(img_path).convert("RGB")
        inputs = processor(text="<DETAILED_CAPTION>", images=image, return_tensors="pt").to("cuda")

        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=256
        )
        caption = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        with open(caption_path, "w") as f:
            f.write(caption)
        print(f"Captioned: {fname}")

def resize_images(input_dir: str, max_size: int = 1024):
    """Resize images to max dimension while preserving aspect ratio."""
    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue

        img_path = os.path.join(input_dir, fname)
        img = Image.open(img_path)

        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            img.save(img_path)
            print(f"Resized: {fname}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("--type", choices=["character", "style", "concept"], default="character")
    parser.add_argument("--caption", action="store_true")
    parser.add_argument("--resize", type=int, default=1024)
    args = parser.parse_args()

    if args.resize:
        resize_images(args.input_dir, args.resize)
    if args.caption:
        caption_images(args.input_dir)

    print("Dataset preparation complete")
```

**Step 3: Create train_lora.py**

```python
#!/usr/bin/env python3
import argparse
import subprocess
import os
import toml

def train(config_path: str, dataset_path: str, output_name: str):
    """Run kohya training with config."""
    config = toml.load(config_path)

    output_dir = "/workspace/outputs"
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "accelerate", "launch",
        "/workspace/sd-scripts/flux_train_network.py",
        f"--pretrained_model_name_or_path={config.get('model', 'black-forest-labs/FLUX.1-dev')}",
        f"--train_data_dir={dataset_path}",
        f"--output_dir={output_dir}",
        f"--output_name={output_name}",
        f"--learning_rate={config.get('learning_rate', 1e-4)}",
        f"--max_train_steps={config.get('max_steps', 1000)}",
        f"--network_dim={config.get('network_dim', 16)}",
        f"--network_alpha={config.get('network_alpha', 16)}",
        "--save_model_as=safetensors",
        "--mixed_precision=bf16",
        "--cache_latents",
    ]

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Sync to GCS
    subprocess.run(["python3", "/workspace/scripts/sync_gcs.py", "push"])
    print(f"Training complete: {output_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    train(args.config, args.dataset, args.name)
```

**Step 4: Commit**

```bash
git add docker/trainer/scripts/
git commit -m "feat: add trainer scripts (sync, prepare, train)"
```

---

### Task 11: Training Configs

**Files:**
- Create: `docker/trainer/configs/character.toml`
- Create: `docker/trainer/configs/style.toml`
- Create: `docker/trainer/configs/concept.toml`

**Step 1: Create character.toml**

```toml
# Character LoRA preset - for faces/people
model = "black-forest-labs/FLUX.1-dev"
learning_rate = 1e-4
max_steps = 1500
network_dim = 32
network_alpha = 16
repeats = 20
```

**Step 2: Create style.toml**

```toml
# Style LoRA preset - for artistic styles
model = "black-forest-labs/FLUX.1-dev"
learning_rate = 5e-5
max_steps = 2000
network_dim = 64
network_alpha = 32
repeats = 10
```

**Step 3: Create concept.toml**

```toml
# Concept LoRA preset - for objects/concepts
model = "black-forest-labs/FLUX.1-dev"
learning_rate = 8e-5
max_steps = 1200
network_dim = 32
network_alpha = 16
repeats = 15
```

**Step 4: Commit**

```bash
git add docker/trainer/configs/
git commit -m "feat: add training config presets"
```

---

### Task 12: ComfyUI Dockerfile

**Files:**
- Create: `docker/comfyui/Dockerfile`
- Create: `docker/comfyui/startup.sh`

**Step 1: Create Dockerfile**

```dockerfile
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3.10 python3-pip git wget \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI

WORKDIR /workspace/ComfyUI
RUN pip3 install --no-cache-dir -r requirements.txt

# Install ComfyUI Manager
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git \
    /workspace/ComfyUI/custom_nodes/ComfyUI-Manager

# Install essential custom nodes
RUN git clone https://github.com/rgthree/rgthree-comfy.git \
    /workspace/ComfyUI/custom_nodes/rgthree-comfy \
    && git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git \
    /workspace/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite \
    && git clone https://github.com/kijai/ComfyUI-Florence2.git \
    /workspace/ComfyUI/custom_nodes/ComfyUI-Florence2

# GCS sync
RUN pip3 install --no-cache-dir google-cloud-storage

COPY startup.sh /workspace/
COPY scripts/ /workspace/scripts/
COPY workflows/ /workspace/ComfyUI/user/default/workflows/

RUN chmod +x /workspace/startup.sh

EXPOSE 8188

CMD ["/workspace/startup.sh"]
```

**Step 2: Create startup.sh**

```bash
#!/bin/bash
set -e

echo "Syncing LoRAs from GCS..."
python3 /workspace/scripts/sync_loras.py

echo "Starting ComfyUI..."
cd /workspace/ComfyUI
python3 main.py --listen 0.0.0.0 --port 8188
```

**Step 3: Commit**

```bash
git add docker/comfyui/
git commit -m "feat: add ComfyUI Docker image"
```

---

### Task 13: ComfyUI Scripts and Workflows

**Files:**
- Create: `docker/comfyui/scripts/sync_loras.py`
- Create: `docker/comfyui/workflows/basic_txt2img.json`

**Step 1: Create sync_loras.py**

```python
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
```

**Step 2: Create basic_txt2img.json**

```json
{
  "last_node_id": 10,
  "last_link_id": 10,
  "nodes": [
    {
      "id": 1,
      "type": "CheckpointLoaderSimple",
      "pos": [50, 100],
      "size": [300, 100],
      "properties": {"Node name for S&R": "Flux Model"},
      "widgets_values": ["flux1-dev.safetensors"]
    },
    {
      "id": 2,
      "type": "LoraLoader",
      "pos": [50, 250],
      "size": [300, 150],
      "properties": {"Node name for S&R": "Your LoRA"},
      "widgets_values": ["", 1.0, 1.0]
    },
    {
      "id": 3,
      "type": "CLIPTextEncode",
      "pos": [400, 100],
      "size": [400, 200],
      "properties": {"Node name for S&R": "Prompt"},
      "widgets_values": ["your prompt here"]
    },
    {
      "id": 4,
      "type": "EmptyLatentImage",
      "pos": [400, 350],
      "size": [300, 100],
      "widgets_values": [1024, 1024, 1]
    },
    {
      "id": 5,
      "type": "KSampler",
      "pos": [850, 100],
      "size": [300, 300],
      "widgets_values": [42, "fixed", 20, 3.5, "euler", "normal", 1.0]
    },
    {
      "id": 6,
      "type": "VAEDecode",
      "pos": [1200, 100],
      "size": [200, 100]
    },
    {
      "id": 7,
      "type": "SaveImage",
      "pos": [1450, 100],
      "size": [300, 300],
      "widgets_values": ["ComfyUI"]
    }
  ],
  "links": [],
  "groups": [
    {"title": "1. Load Model & LoRA", "bounding": [30, 50, 340, 380]},
    {"title": "2. Enter Prompt", "bounding": [380, 50, 440, 420]},
    {"title": "3. Generate", "bounding": [830, 50, 320, 380]},
    {"title": "4. Save", "bounding": [1180, 50, 590, 380]}
  ]
}
```

**Step 3: Commit**

```bash
git add docker/comfyui/scripts/ docker/comfyui/workflows/
git commit -m "feat: add ComfyUI sync script and basic workflow"
```

---

## Phase 4: Frontend

### Task 14: React App Setup

**Files:**
- Create: `ui/frontend/package.json`
- Create: `ui/frontend/vite.config.js`
- Create: `ui/frontend/index.html`
- Create: `ui/frontend/src/main.jsx`
- Create: `ui/frontend/src/App.jsx`
- Create: `ui/frontend/tailwind.config.js`
- Create: `ui/frontend/postcss.config.js`
- Create: `ui/frontend/src/index.css`

**Step 1: Create package.json**

```json
{
  "name": "lora-cloud-ui",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0",
    "vite": "^5.0.10"
  }
}
```

**Step 2: Create vite.config.js**

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

**Step 3: Create tailwind.config.js**

```javascript
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: {} },
  plugins: []
}
```

**Step 4: Create postcss.config.js**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {}
  }
}
```

**Step 5: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>LoRA Cloud</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
```

**Step 6: Create src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Step 7: Create src/main.jsx**

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

**Step 8: Create src/App.jsx**

```jsx
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Datasets from './pages/Datasets'
import Training from './pages/Training'
import Loras from './pages/Loras'
import Generate from './pages/Generate'

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/datasets', label: 'Datasets' },
  { path: '/training', label: 'Training' },
  { path: '/loras', label: 'LoRAs' },
  { path: '/generate', label: 'Generate' }
]

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-900 text-white">
        <nav className="bg-gray-800 px-6 py-4">
          <div className="flex gap-6">
            <span className="font-bold text-xl">LoRA Cloud</span>
            {navItems.map(item => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `px-3 py-1 rounded ${isActive ? 'bg-blue-600' : 'hover:bg-gray-700'}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>
        <main className="p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/datasets" element={<Datasets />} />
            <Route path="/training" element={<Training />} />
            <Route path="/loras" element={<Loras />} />
            <Route path="/generate" element={<Generate />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
```

**Step 9: Commit**

```bash
git add ui/frontend/
git commit -m "feat: initialize React frontend with Tailwind"
```

---

### Task 15: Dashboard Page

**Files:**
- Create: `ui/frontend/src/pages/Dashboard.jsx`
- Create: `ui/frontend/src/hooks/useApi.js`

**Step 1: Create useApi.js**

```jsx
import { useState, useEffect } from 'react'

export function useApi(endpoint) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refetch = async () => {
    setLoading(true)
    try {
      const res = await fetch(`/api${endpoint}`)
      if (!res.ok) throw new Error('API error')
      setData(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refetch() }, [endpoint])

  return { data, loading, error, refetch }
}

export async function apiPost(endpoint, body) {
  const res = await fetch(`/api${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  if (!res.ok) throw new Error('API error')
  return res.json()
}

export async function apiDelete(endpoint) {
  const res = await fetch(`/api${endpoint}`, { method: 'DELETE' })
  if (!res.ok) throw new Error('API error')
  return res.json()
}
```

**Step 2: Create Dashboard.jsx**

```jsx
import { useApi, apiPost, apiDelete } from '../hooks/useApi'

export default function Dashboard() {
  const { data: instances, loading, refetch } = useApi('/instances')

  const launchTrainer = async () => {
    await apiPost('/instances/launch', {
      gpu_type: 'A100',
      image: 'your-dockerhub/flux-lora-trainer:latest',
      max_price: 1.5
    })
    refetch()
  }

  const launchComfy = async () => {
    await apiPost('/instances/launch', {
      gpu_type: 'RTX 4090',
      image: 'your-dockerhub/flux-comfyui:latest',
      max_price: 0.5
    })
    refetch()
  }

  const stopInstance = async (id) => {
    await apiDelete(`/instances/${id}`)
    refetch()
  }

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="flex gap-4 mb-8">
        <button
          onClick={launchTrainer}
          className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded"
        >
          Launch Training Instance
        </button>
        <button
          onClick={launchComfy}
          className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
        >
          Launch ComfyUI
        </button>
      </div>

      <h2 className="text-xl font-semibold mb-4">Active Instances</h2>
      {instances?.length === 0 ? (
        <p className="text-gray-400">No running instances</p>
      ) : (
        <div className="grid gap-4">
          {instances?.map(inst => (
            <div key={inst.id} className="bg-gray-800 p-4 rounded flex justify-between items-center">
              <div>
                <p className="font-medium">{inst.gpu_name}</p>
                <p className="text-sm text-gray-400">
                  ${inst.dph_total?.toFixed(2)}/hr | {inst.status}
                </p>
              </div>
              <div className="flex gap-2">
                <button className="bg-blue-600 px-3 py-1 rounded text-sm">
                  Connect
                </button>
                <button
                  onClick={() => stopInstance(inst.id)}
                  className="bg-red-600 px-3 py-1 rounded text-sm"
                >
                  Stop
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

**Step 3: Commit**

```bash
git add ui/frontend/src/pages/Dashboard.jsx ui/frontend/src/hooks/
git commit -m "feat: add Dashboard page with instance management"
```

---

### Task 16: Remaining Pages (Stubs)

**Files:**
- Create: `ui/frontend/src/pages/Datasets.jsx`
- Create: `ui/frontend/src/pages/Training.jsx`
- Create: `ui/frontend/src/pages/Loras.jsx`
- Create: `ui/frontend/src/pages/Generate.jsx`

**Step 1: Create Datasets.jsx**

```jsx
import { useApi } from '../hooks/useApi'

export default function Datasets() {
  const { data: datasets, loading } = useApi('/datasets')

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Datasets</h1>
      <div className="mb-6">
        <label className="block bg-gray-800 p-8 rounded border-2 border-dashed border-gray-600 text-center cursor-pointer hover:border-gray-500">
          <input type="file" multiple className="hidden" />
          Drop images here or click to upload
        </label>
      </div>
      <div className="grid gap-4">
        {datasets?.map(ds => (
          <div key={ds.name} className="bg-gray-800 p-4 rounded">
            <p className="font-medium">{ds.name}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Step 2: Create Training.jsx**

```jsx
export default function Training() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Training</h1>
      <p className="text-gray-400">Training queue and history will appear here.</p>
    </div>
  )
}
```

**Step 3: Create Loras.jsx**

```jsx
import { useApi } from '../hooks/useApi'

export default function Loras() {
  const { data: loras, loading } = useApi('/loras')

  if (loading) return <div>Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Trained LoRAs</h1>
      <div className="grid gap-4">
        {loras?.map(lora => (
          <div key={lora.name} className="bg-gray-800 p-4 rounded flex justify-between">
            <div>
              <p className="font-medium">{lora.name}</p>
              <p className="text-sm text-gray-400">
                {(lora.size / 1024 / 1024).toFixed(1)} MB
              </p>
            </div>
            <button className="bg-blue-600 px-3 py-1 rounded text-sm">
              Download
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Step 4: Create Generate.jsx**

```jsx
export default function Generate() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Generate</h1>
      <p className="text-gray-400">Launch ComfyUI from the Dashboard to generate images.</p>
    </div>
  )
}
```

**Step 5: Commit**

```bash
git add ui/frontend/src/pages/
git commit -m "feat: add Datasets, Training, LoRAs, Generate pages"
```

---

## Phase 5: Documentation

### Task 17: Setup Guide

**Files:**
- Create: `docs/setup.md`

**Step 1: Create setup.md**

```markdown
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
```

**Step 2: Commit**

```bash
git add docs/setup.md
git commit -m "docs: add setup guide"
```

---

## Summary

**Total Tasks:** 17
**Phases:**
1. Project Foundation (Tasks 1-5)
2. API Endpoints (Tasks 6-8)
3. Docker Images (Tasks 9-13)
4. Frontend (Tasks 14-16)
5. Documentation (Task 17)

---

Plan complete and saved to `docs/plans/2026-01-29-lora-cloud-implementation.md`.

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
