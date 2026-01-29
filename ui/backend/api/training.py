from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/training", tags=["training"])

# In-memory store for training jobs (would use a DB in production)
training_jobs: dict[str, dict] = {}

class TrainingJobCreate(BaseModel):
    instance_id: int
    dataset_name: str
    lora_name: str
    base_model: str = "black-forest-labs/FLUX.1-dev"
    lora_type: str = "character"
    steps: int = 1000
    learning_rate: float = 1e-4
    batch_size: int = 1
    resolution: int = 512
    network_dim: int = 32
    network_alpha: int = 16

class TrainingJobUpdate(BaseModel):
    status: Optional[str] = None
    current_step: Optional[int] = None
    error: Optional[str] = None

@router.get("")
def list_jobs():
    """List all training jobs."""
    return list(training_jobs.values())

@router.post("")
def create_job(job: TrainingJobCreate):
    """Create a new training job."""
    job_id = str(uuid.uuid4())[:8]
    training_jobs[job_id] = {
        "id": job_id,
        "instance_id": job.instance_id,
        "dataset_name": job.dataset_name,
        "lora_name": job.lora_name,
        "base_model": job.base_model,
        "lora_type": job.lora_type,
        "steps": job.steps,
        "learning_rate": job.learning_rate,
        "batch_size": job.batch_size,
        "resolution": job.resolution,
        "network_dim": job.network_dim,
        "network_alpha": job.network_alpha,
        "status": "pending",
        "current_step": 0,
        "error": None,
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "completed_at": None
    }
    return training_jobs[job_id]

@router.get("/{job_id}")
def get_job(job_id: str):
    """Get training job details."""
    if job_id not in training_jobs:
        raise HTTPException(404, "Job not found")
    return training_jobs[job_id]

@router.patch("/{job_id}")
def update_job(job_id: str, update: TrainingJobUpdate):
    """Update training job status."""
    if job_id not in training_jobs:
        raise HTTPException(404, "Job not found")

    job = training_jobs[job_id]
    if update.status:
        job["status"] = update.status
        if update.status == "running" and not job["started_at"]:
            job["started_at"] = datetime.utcnow().isoformat()
        elif update.status in ["completed", "failed"]:
            job["completed_at"] = datetime.utcnow().isoformat()
    if update.current_step is not None:
        job["current_step"] = update.current_step
    if update.error:
        job["error"] = update.error

    return job

@router.delete("/{job_id}")
def delete_job(job_id: str):
    """Delete a training job."""
    if job_id not in training_jobs:
        raise HTTPException(404, "Job not found")
    del training_jobs[job_id]
    return {"status": "deleted"}
