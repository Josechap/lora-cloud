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
