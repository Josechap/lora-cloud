# LoRA Cloud ☁️

A self-hosted platform for training Flux LoRAs on vast.ai GPUs with a modern web interface.

## Features

- **GPU Instance Management** - Launch and manage vast.ai instances directly from the UI
- **Dataset Management** - Upload and organize training images with drag-and-drop
- **Training Jobs** - Configure and monitor LoRA training with kohya_ss/sd-scripts
- **LoRA Library** - Download and manage your trained LoRAs
- **ComfyUI Integration** - Connect to ComfyUI via SSH tunnel for image generation

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   FastAPI       │────▶│   vast.ai API   │
│   (localhost    │     │   Backend       │     │   (GPU rental)  │
│    :3000)       │     │   (:8000)       │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Google Cloud   │
                        │  Storage        │
                        │  (datasets/     │
                        │   loras)        │
                        └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- vast.ai account with API key
- Google Cloud account with a storage bucket

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Josechap/lora-cloud.git
   cd lora-cloud
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # - VAST_API_KEY: Your vast.ai API key
   # - GCS_BUCKET: Your GCS bucket name
   # - GCS_CREDENTIALS_PATH: Path to service account JSON
   ```

3. **Start the backend**
   ```bash
   cd ui/backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```

4. **Start the frontend**
   ```bash
   cd ui/frontend
   npm install
   npm run dev
   ```

5. **Open the UI** at http://localhost:3000

## Usage

### 1. Launch an Instance

From the Dashboard, select a GPU type and click "Launch Training Instance" or "Launch ComfyUI".

### 2. Upload a Dataset

Go to Datasets, enter a name, and drag-and-drop your training images.

### 3. Start Training

Go to Training, select your dataset, configure parameters, and click "Start Training".

### 4. Generate Images

Go to Generate, connect to a ComfyUI instance, and use your trained LoRA.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/instances` | GET | List running instances |
| `/api/instances/launch` | POST | Launch new instance |
| `/api/instances/{id}` | DELETE | Terminate instance |
| `/api/instances/{id}/ssh` | GET | Get SSH connection info |
| `/api/datasets` | GET | List datasets |
| `/api/datasets/{name}/upload` | POST | Upload images |
| `/api/loras` | GET | List trained LoRAs |
| `/api/training` | GET/POST | Manage training jobs |

## Training Configuration

Default training parameters optimized for Flux LoRAs:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Steps | 1000 | Training iterations |
| Learning Rate | 1e-4 | Optimizer learning rate |
| Resolution | 512 | Training image size |
| Network Dim | 32 | LoRA rank |
| Network Alpha | 16 | LoRA alpha scaling |

## Project Structure

```
lora-cloud/
├── ui/
│   ├── backend/          # FastAPI backend
│   │   ├── api/          # API endpoints
│   │   ├── services/     # Business logic
│   │   └── main.py       # App entry
│   └── frontend/         # React frontend
│       ├── src/
│       │   ├── pages/    # Page components
│       │   └── hooks/    # React hooks
│       └── package.json
├── docker/               # Docker images
│   ├── trainer/          # Training image
│   └── comfyui/          # ComfyUI image
└── docs/                 # Documentation
```

## License

MIT
