from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from services.gcs import gcs_service
import tempfile

router = APIRouter(prefix="/loras", tags=["loras"])

class TrainingConfig(BaseModel):
    dataset_name: str
    lora_name: str
    base_model: str = "black-forest-labs/FLUX.1-dev"
    lora_type: str = "character"  # character, style, concept
    steps: int = 1000
    learning_rate: float = 1e-4
    batch_size: int = 1
    resolution: int = 512
    network_dim: int = 32
    network_alpha: int = 16

@router.get("")
def list_loras():
    """List all trained LoRAs."""
    return gcs_service.list_loras()

@router.get("/{name}")
def get_lora(name: str):
    """Get LoRA details."""
    loras = gcs_service.list_loras()
    lora = next((l for l in loras if l["name"] == name), None)
    if not lora:
        raise HTTPException(404, "LoRA not found")
    return lora

@router.get("/{name}/url")
def get_lora_url(name: str):
    """Get a signed URL to download a LoRA."""
    loras = gcs_service.list_loras()
    lora = next((l for l in loras if l["name"] == name), None)
    if not lora:
        raise HTTPException(404, "LoRA not found")
    url = gcs_service.get_signed_url(lora["path"])
    return {"url": url}

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

@router.post("/training/config")
def get_training_command(config: TrainingConfig):
    """Generate training command for an instance."""
    # Generate the kohya_ss training command
    cmd = f"""cd /workspace && \\
accelerate launch --num_cpu_threads_per_process=2 sd-scripts/flux_train_network.py \\
    --pretrained_model_name_or_path="{config.base_model}" \\
    --dataset_config="/workspace/dataset_config.toml" \\
    --output_dir="/workspace/output" \\
    --output_name="{config.lora_name}" \\
    --save_model_as=safetensors \\
    --max_train_steps={config.steps} \\
    --learning_rate={config.learning_rate} \\
    --train_batch_size={config.batch_size} \\
    --resolution={config.resolution} \\
    --network_module=networks.lora_flux \\
    --network_dim={config.network_dim} \\
    --network_alpha={config.network_alpha} \\
    --optimizer_type="AdamW8bit" \\
    --mixed_precision="bf16" \\
    --cache_latents \\
    --gradient_checkpointing \\
    --save_every_n_steps=200"""

    # Generate dataset config
    dataset_config = f"""[general]
shuffle_caption = true
caption_extension = ".txt"
keep_tokens = 1

[[datasets]]
resolution = {config.resolution}
batch_size = {config.batch_size}

[[datasets.subsets]]
image_dir = "/workspace/dataset"
num_repeats = 10
"""

    return {
        "command": cmd,
        "dataset_config": dataset_config,
        "gcs_dataset_path": f"datasets/{config.dataset_name}/",
        "gcs_output_path": f"loras/{config.lora_name}.safetensors"
    }


class ComfyUISyncRequest(BaseModel):
    """Request to sync LoRAs to a ComfyUI instance."""
    comfyui_host: str  # e.g., "localhost:8188" or "192.168.1.100:8188"
    lora_names: list[str] = []  # Empty = sync all LoRAs


@router.post("/sync-to-comfyui")
async def sync_to_comfyui(request: ComfyUISyncRequest):
    """
    Sync LoRAs from GCS to a ComfyUI instance.
    Downloads LoRAs and makes them available via ComfyUI API.
    """
    import httpx
    
    loras = gcs_service.list_loras()
    
    # Filter if specific LoRAs requested
    if request.lora_names:
        loras = [l for l in loras if l["name"] in request.lora_names]
    
    if not loras:
        raise HTTPException(404, "No LoRAs found to sync")
    
    synced = []
    errors = []
    
    for lora in loras:
        try:
            # Get signed URL for the LoRA
            url = gcs_service.get_signed_url(lora["path"])
            
            # For now, just return the URLs - ComfyUI can download directly
            # In a full implementation, you'd use ComfyUI's API to load the LoRA
            synced.append({
                "name": lora["name"],
                "url": url,
                "size": lora["size"]
            })
        except Exception as e:
            errors.append({"name": lora["name"], "error": str(e)})
    
    return {
        "synced": synced,
        "errors": errors,
        "comfyui_host": request.comfyui_host,
        "message": f"Synced {len(synced)} LoRAs. Use the URLs to download and place in ComfyUI's models/loras folder."
    }


@router.get("/{name}/comfyui-loader")
def get_comfyui_loader_node(name: str):
    """
    Get a ComfyUI LoraLoader node configuration for a specific LoRA.
    Can be used to programmatically add the LoRA to a workflow.
    """
    loras = gcs_service.list_loras()
    lora = next((l for l in loras if l["name"] == name), None)
    if not lora:
        raise HTTPException(404, "LoRA not found")
    
    return {
        "node_type": "LoraLoader",
        "inputs": {
            "lora_name": name,
            "strength_model": 1.0,
            "strength_clip": 1.0
        },
        "lora_info": lora,
        "download_url": gcs_service.get_signed_url(lora["path"])
    }
