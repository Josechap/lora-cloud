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
