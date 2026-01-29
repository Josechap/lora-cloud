# LoRA Cloud - Design Document

**Date:** 2026-01-29
**Status:** Approved

## Overview

A complete system for training Flux LoRAs and generating images using vast.ai cloud GPUs, with a local web UI for management.

## Core Requirements

- **Base Model:** Flux
- **LoRA Types:** Character, Style, Concept (flexible)
- **Training Framework:** kohya_ss / sd-scripts
- **Image Generation:** ComfyUI with pre-built workflow templates
- **Deployment:** Docker images on vast.ai
- **Storage:** Google Cloud Storage (auto-sync)
- **Dataset Tools:** Full pipeline (collection, cropping, captioning)
- **Access:** SSH + port forwarding
- **Control:** Local web UI dashboard

---

## Architecture

### Two Docker Images

1. **Training Image (`flux-lora-trainer`)**
   - kohya_ss/sd-scripts with Flux support
   - Dataset preparation tools (BLIP-2, Florence-2 for captioning)
   - Image preprocessing (cropping, resizing, face detection)
   - GCS sync for datasets and trained LoRAs
   - Optimized for high-VRAM GPUs (A100 40GB+, H100)

2. **Inference Image (`flux-comfyui`)**
   - ComfyUI with Flux nodes and custom nodes
   - Pre-built workflow templates
   - Trained LoRAs synced from GCS
   - Can run on smaller GPUs (4090, A6000)

### GCS Bucket Structure

```
your-bucket/
├── datasets/          # Training images + captions
├── loras/             # Trained LoRA outputs
├── models/            # Base Flux models (cached)
└── workflows/         # ComfyUI workflow templates
```

---

## Training Image Details

### Base Setup
- Ubuntu 22.04 + CUDA 12.1 + Python 3.10
- kohya_ss/sd-scripts (latest Flux-compatible branch)
- Automatic GCS sync on startup and after each training run

### Dataset Preparation Tools

| Tool | Purpose |
|------|---------|
| Florence-2 | Auto-captioning (best quality for Flux) |
| BLIP-2 | Alternative captioner |
| face_recognition | Face detection + cropping for character LoRAs |
| rembg | Background removal |
| PIL/OpenCV | Resize, crop, aspect ratio bucketing |

### Directory Structure

```
/workspace/
├── scripts/
│   ├── prepare_dataset.py    # Full pipeline: crop, caption, organize
│   ├── train_lora.py         # Wrapper with sane Flux defaults
│   ├── sync_gcs.py           # Push/pull from cloud storage
│   └── validate_dataset.py   # Check for issues before training
├── datasets/                  # Synced from GCS
├── outputs/                   # Trained LoRAs (synced to GCS)
└── configs/
    ├── character.toml        # Preset for character LoRAs
    ├── style.toml            # Preset for style LoRAs
    └── concept.toml          # Preset for concept LoRAs
```

### Training Presets
- **Character:** higher learning rate, more repeats, face-focused cropping
- **Style:** lower learning rate, more steps, diverse aspect ratios
- **Concept:** balanced settings, object-focused cropping

---

## Inference Image Details

### Base Setup
- Ubuntu 22.04 + CUDA 12.1 + Python 3.10
- ComfyUI (latest) + ComfyUI Manager
- Flux model support (fp8/fp16 quantized options)
- Auto-sync LoRAs from GCS on startup

### Pre-installed Custom Nodes

| Node Pack | Purpose |
|-----------|---------|
| ComfyUI-Manager | Easy node installation |
| ComfyUI-Florence2 | Captioning within workflows |
| ComfyUI-KJNodes | Utility nodes |
| ComfyUI-Impact-Pack | Face detection, upscaling |
| ComfyUI-ControlNet-Aux | Preprocessors for ControlNet |
| rgthree-comfy | Quality of life nodes, better UI |
| ComfyUI-Custom-Scripts | Workflow organization |

### Pre-built Workflow Templates

| Workflow | Description |
|----------|-------------|
| `basic_txt2img.json` | Simple text-to-image with LoRA slot |
| `lora_comparison.json` | Test LoRA at different strengths side-by-side |
| `img2img_refine.json` | Refine/iterate on generated images |
| `batch_generation.json` | Generate multiple variations |
| `controlnet_pose.json` | Pose-guided generation for characters |
| `upscale_4x.json` | Upscale outputs with detail enhancement |

### Directory Structure

```
/workspace/
├── ComfyUI/
│   ├── models/
│   │   ├── unet/           # Flux model
│   │   ├── clip/           # Text encoders
│   │   ├── vae/            # VAE
│   │   └── loras/          # Synced from GCS
│   ├── input/              # Upload images here
│   └── output/             # Generated images
├── workflows/              # Your saved workflows
└── scripts/
    └── sync_loras.py       # Pull latest LoRAs from GCS
```

---

## Control Panel UI

### Tech Stack
- **Backend:** Python FastAPI
- **Frontend:** React + Tailwind
- **Local:** Runs at http://localhost:3000

### Dashboard Tabs

#### 1. Instances
- Active instances (GPU, cost/hr, uptime, status)
- Quick launch buttons for training/inference
- Cost tracking (today/month)
- Actions: Connect, Stop, View Logs

#### 2. Datasets
- List all datasets in GCS with thumbnails
- Preview images and captions
- Edit captions inline
- Drag & drop upload
- Preparation pipeline: Select type → Auto-caption → Review → Save

#### 3. Training
- Training queue and history
- Live progress (step, loss graph, sample images)
- Config editor with presets
- Comparison of different training runs

#### 4. LoRAs
- All trained LoRAs with metadata
- Download, delete, test actions
- Quick test: generate sample image with LoRA

#### 5. Generate
- ComfyUI instance status
- Launch/stop/open ComfyUI
- Recent outputs gallery
- Workflow template loader

### Features
- WebSocket for real-time updates
- macOS notifications for training completion
- Budget warnings and auto-terminate options
- Background training mode (disconnect and walk away)

---

## Automation Features

### CLI Tool (`lora-cloud`)

```bash
# Instance management
lora-cloud train start --gpu a100 --dataset my_character --type character
lora-cloud train status
lora-cloud train stop
lora-cloud comfy start --gpu 4090
lora-cloud comfy stop

# Dataset management
lora-cloud dataset upload ./images --name my_character
lora-cloud dataset prepare my_character --type character --caption florence
lora-cloud dataset list

# LoRA management
lora-cloud lora list
lora-cloud lora download my_lora
lora-cloud lora delete old_lora
```

### Cost Controls
- Max hourly budget limit
- Auto-terminate after N hours
- Spot instance preference
- Cheapest GPU auto-selection

### Notifications
- Training complete → macOS notification + optional webhook
- Budget limit warning
- Spot instance preemption → auto-save checkpoint

---

## Project Structure

```
lora-cloud/
├── docker/
│   ├── trainer/
│   │   ├── Dockerfile
│   │   ├── scripts/
│   │   │   ├── prepare_dataset.py
│   │   │   ├── train_lora.py
│   │   │   ├── sync_gcs.py
│   │   │   └── validate_dataset.py
│   │   └── configs/
│   │       ├── character.toml
│   │       ├── style.toml
│   │       └── concept.toml
│   └── comfyui/
│       ├── Dockerfile
│       ├── workflows/
│       │   ├── basic_txt2img.json
│       │   ├── lora_comparison.json
│       │   ├── img2img_refine.json
│       │   └── ...
│       └── scripts/
│           └── sync_loras.py
├── ui/
│   ├── backend/              # FastAPI
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── instances.py
│   │   │   ├── datasets.py
│   │   │   ├── training.py
│   │   │   ├── loras.py
│   │   │   └── websocket.py
│   │   └── services/
│   │       ├── vast.py       # vast.ai API wrapper
│   │       ├── gcs.py        # Google Cloud Storage
│   │       └── ssh.py        # SSH tunnel management
│   └── frontend/             # React + Tailwind
│       ├── src/
│       │   ├── pages/
│       │   │   ├── Dashboard.jsx
│       │   │   ├── Datasets.jsx
│       │   │   ├── Training.jsx
│       │   │   ├── Loras.jsx
│       │   │   └── Generate.jsx
│       │   └── components/
│       └── public/
├── cli/
│   └── lora_cloud/           # CLI tool
│       ├── __init__.py
│       └── main.py
├── docs/
│   ├── setup.md              # Initial GCS + vast.ai setup
│   ├── training-guide.md     # How to train good LoRAs
│   └── troubleshooting.md
├── requirements.txt
├── docker-compose.yml        # Local dev setup
└── README.md
```

---

## Deliverables

1. Two Docker images ready to push/use on vast.ai
2. Local web UI to control everything
3. CLI for scripting/automation
4. Pre-built ComfyUI workflows
5. Training presets tuned for Flux
6. Full documentation
