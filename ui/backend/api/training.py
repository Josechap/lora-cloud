from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from services.vast import vast_service
from services.ssh import ssh_service
from services.gcs import gcs_service
from config import settings
import uuid
import asyncio
import threading
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def run_training_thread(job_id: str, job: dict, ssh_host: str, ssh_port: int):
    """Run training in a background thread."""
    logger.info(f"[{job_id}] Starting training thread for {job['lora_name']}")
    logger.info(f"[{job_id}] SSH target: {ssh_host}:{ssh_port}")
    
    try:
        # Update status to running
        job["status"] = "running"
        job["started_at"] = datetime.utcnow().isoformat()
        logger.info(f"[{job_id}] Status set to running")

        # Step 1: Setup workspace
        logger.info(f"[{job_id}] Step 1: Setting up workspace...")
        setup_cmd = f"""
mkdir -p /workspace/dataset /workspace/output /workspace/logs
echo "Workspace ready"
"""
        exit_code, stdout, stderr = ssh_service.exec_command(ssh_host, ssh_port, setup_cmd)
        logger.info(f"[{job_id}] Setup result: exit_code={exit_code}, stdout={stdout[:100] if stdout else 'empty'}")
        if stderr:
            logger.warning(f"[{job_id}] Setup stderr: {stderr}")
        if exit_code != 0:
            raise Exception(f"Setup failed: {stderr}")

        # Step 2: Install dependencies (if not already installed)
        logger.info(f"[{job_id}] Step 2: Checking/installing dependencies...")
        install_cmd = """
if ! command -v accelerate &> /dev/null; then
    pip install accelerate transformers datasets bitsandbytes safetensors -q
fi
echo "Dependencies ready"
"""
        exit_code, stdout, stderr = ssh_service.exec_command(ssh_host, ssh_port, install_cmd, timeout=600)
        logger.info(f"[{job_id}] Dependencies result: exit_code={exit_code}, stdout={stdout[:100] if stdout else 'empty'}")
        if stderr:
            logger.warning(f"[{job_id}] Dependencies stderr: {stderr[:200] if stderr else 'empty'}")

        # Step 3: Download dataset from GCS (simulated for now - real impl would use gsutil)
        job["current_step"] = 10
        logger.info(f"[{job_id}] Step 3: Dataset prep (current_step=10)")

        # Step 4: Run training (simplified - real training would use kohya_ss)
        # For demo, we'll simulate training progress
        logger.info(f"[{job_id}] Step 4: Starting training simulation...")
        train_cmd = f"""
echo "Starting training for {job['lora_name']}"
for i in $(seq 1 {job['steps']}); do
    if [ $((i % 100)) -eq 0 ]; then
        echo "STEP:$i"
    fi
    sleep 0.01
done
echo "Training complete"
# Create a dummy LoRA file with some content (for demo purposes)
# In real training, this would be the actual trained model
head -c 1024 /dev/urandom > /workspace/output/{job['lora_name']}.safetensors
echo "LoRA file created: $(ls -la /workspace/output/{job['lora_name']}.safetensors)"
"""
        logger.info(f"[{job_id}] Executing async training command...")
        client, stdout_stream, stderr_stream = ssh_service.exec_command_async(ssh_host, ssh_port, train_cmd)
        logger.info(f"[{job_id}] Async command started, reading output...")

        try:
            line_count = 0
            for line in stdout_stream:
                line = line.strip()
                line_count += 1
                if line_count <= 5 or line_count % 10 == 0:
                    logger.info(f"[{job_id}] Output line {line_count}: {line}")
                # Parse step updates
                match = re.search(r'STEP:(\d+)', line)
                if match:
                    step = int(match.group(1))
                    job["current_step"] = step
                    logger.info(f"[{job_id}] Progress: step {step}/{job['steps']}")
            logger.info(f"[{job_id}] Finished reading output, total lines: {line_count}")
        finally:
            client.close()
            logger.info(f"[{job_id}] SSH client closed")

        # Step 5: Upload LoRA to GCS
        logger.info(f"[{job_id}] Step 5: Uploading LoRA to GCS...")
        job["status"] = "uploading"
        
        lora_filename = f"{job['lora_name']}.safetensors"
        remote_lora_path = f"/workspace/output/{lora_filename}"
        
        # Download LoRA from remote instance via SSH (using cat and base64)
        import tempfile
        import base64
        
        # Check if file exists and get its size
        check_cmd = f"ls -la {remote_lora_path} && wc -c < {remote_lora_path}"
        exit_code, stdout, stderr = ssh_service.exec_command(ssh_host, ssh_port, check_cmd)
        logger.info(f"[{job_id}] LoRA file check: {stdout}")
        
        if exit_code == 0:
            # Download the file using base64 encoding
            download_cmd = f"base64 {remote_lora_path}"
            exit_code, stdout, stderr = ssh_service.exec_command(ssh_host, ssh_port, download_cmd, timeout=300)
            
            if exit_code == 0 and stdout:
                # Decode and save locally, then upload to GCS
                with tempfile.NamedTemporaryFile(delete=False, suffix='.safetensors') as tmp:
                    tmp.write(base64.b64decode(stdout))
                    tmp.flush()
                    local_path = tmp.name
                
                # Upload to GCS
                gcs_path = f"loras/{lora_filename}"
                gcs_service.upload_file(local_path, gcs_path)
                logger.info(f"[{job_id}] LoRA uploaded to GCS: {gcs_path}")
                
                # Clean up temp file
                import os
                os.unlink(local_path)
                
                job["gcs_path"] = gcs_path
            else:
                logger.warning(f"[{job_id}] Failed to download LoRA: {stderr}")
        else:
            logger.warning(f"[{job_id}] LoRA file not found on remote: {stderr}")

        # Training complete
        job["status"] = "completed"
        job["current_step"] = job["steps"]
        job["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"[{job_id}] Training completed successfully!")

    except Exception as e:
        logger.error(f"[{job_id}] Training failed with error: {e}", exc_info=True)
        job["status"] = "failed"
        job["error"] = str(e)
        job["completed_at"] = datetime.utcnow().isoformat()


async def start_training(job_id: str, job: dict):
    """Start training on the remote instance."""
    logger.info(f"[{job_id}] start_training called for instance {job['instance_id']}")
    
    try:
        # Get instance SSH info
        logger.info(f"[{job_id}] Fetching instance info from vast.ai...")
        instance = await vast_service.get_instance(job["instance_id"])
        if not instance:
            logger.error(f"[{job_id}] Instance not found!")
            job["status"] = "failed"
            job["error"] = "Instance not found"
            return

        logger.info(f"[{job_id}] Instance state: {instance.get('cur_state')}")
        if instance.get("cur_state") != "running":
            logger.error(f"[{job_id}] Instance not ready: {instance.get('cur_state')}")
            job["status"] = "failed"
            job["error"] = f"Instance not ready: {instance.get('cur_state')}"
            return

        ssh_host = instance.get("ssh_host")
        ssh_port = instance.get("ssh_port")
        logger.info(f"[{job_id}] SSH info: {ssh_host}:{ssh_port}")

        if not ssh_host or not ssh_port:
            logger.error(f"[{job_id}] SSH not available yet")
            job["status"] = "failed"
            job["error"] = "Instance SSH not available yet"
            return

        # Run training in background thread
        logger.info(f"[{job_id}] Starting background training thread...")
        thread = threading.Thread(
            target=run_training_thread,
            args=(job_id, job, ssh_host, ssh_port)
        )
        thread.daemon = True
        thread.start()
        logger.info(f"[{job_id}] Background thread started")

    except Exception as e:
        logger.error(f"[{job_id}] start_training failed: {e}", exc_info=True)
        job["status"] = "failed"
        job["error"] = str(e)

@router.get("")
def list_jobs():
    """List all training jobs."""
    return list(training_jobs.values())

@router.post("")
async def create_job(job: TrainingJobCreate, background_tasks: BackgroundTasks):
    """Create and start a new training job."""
    job_id = str(uuid.uuid4())[:8]
    logger.info(f"[{job_id}] Creating new training job: {job.lora_name}")
    
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

    # Start training in background
    logger.info(f"[{job_id}] Adding start_training to background tasks")
    background_tasks.add_task(start_training, job_id, training_jobs[job_id])

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

@router.post("/{job_id}/start")
async def start_job(job_id: str, background_tasks: BackgroundTasks):
    """Start or restart a training job."""
    if job_id not in training_jobs:
        raise HTTPException(404, "Job not found")

    job = training_jobs[job_id]
    if job["status"] == "running":
        raise HTTPException(400, "Job is already running")

    # Reset job state
    job["status"] = "pending"
    job["current_step"] = 0
    job["error"] = None
    job["started_at"] = None
    job["completed_at"] = None

    # Start training
    logger.info(f"[{job_id}] Restarting job")
    background_tasks.add_task(start_training, job_id, job)
    return job

@router.delete("/{job_id}")
def delete_job(job_id: str):
    """Delete a training job."""
    if job_id not in training_jobs:
        raise HTTPException(404, "Job not found")
    del training_jobs[job_id]
    logger.info(f"[{job_id}] Job deleted")
    return {"status": "deleted"}
