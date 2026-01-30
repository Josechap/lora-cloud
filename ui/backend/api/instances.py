from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.vast import vast_service
from services.ssh import ssh_service
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/instances", tags=["instances"])

class LaunchRequest(BaseModel):
    gpu_type: str = "RTX 4090"
    image: str
    disk_gb: int = 50
    max_price: float = 1.0

class TunnelRequest(BaseModel):
    remote_port: int
    local_port: int
    ssh_key_path: Optional[str] = None  # Uses default key if not provided

class GPUSearchRequest(BaseModel):
    gpu_type: str = "RTX 4090"
    min_gpu_ram: int = 24
    max_price: float = 1.0

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
        raise HTTPException(404, f"No {req.gpu_type} GPUs available under ${req.max_price}/hr")

    # Sort by price and try up to 3 offers (in case some are taken)
    sorted_offers = sorted(offers, key=lambda x: x.get("dph_total", 999))

    last_error = None
    for offer in sorted_offers[:3]:
        try:
            result = await vast_service.rent_instance(
                offer_id=offer["id"],
                image=req.image,
                disk_gb=req.disk_gb
            )
            return result
        except Exception as e:
            last_error = str(e)
            continue

    raise HTTPException(503, f"Could not rent instance: {last_error}")

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
    logger.info(f"Creating tunnel for instance {instance_id}: remote={req.remote_port}, local={req.local_port}")
    
    instance = await vast_service.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, "Instance not found")

    ssh_host = instance.get("ssh_host")
    ssh_port = instance.get("ssh_port")
    
    if not ssh_host or not ssh_port:
        raise HTTPException(400, f"Instance SSH not available. State: {instance.get('cur_state')}")
    
    logger.info(f"Instance SSH info: {ssh_host}:{ssh_port}")
    
    try:
        local_port = ssh_service.create_tunnel(
            instance_id=instance_id,
            ssh_host=ssh_host,
            ssh_port=ssh_port,
            remote_port=req.remote_port,
            local_port=req.local_port,
            ssh_key_path=req.ssh_key_path  # None = use default key
        )
        logger.info(f"Tunnel created successfully on local port {local_port}")
        return {"local_port": local_port}
    except Exception as e:
        logger.error(f"Failed to create tunnel: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to create tunnel: {str(e)}")

@router.delete("/{instance_id}/tunnel")
async def close_tunnel(instance_id: int):
    """Close SSH tunnel."""
    ssh_service.close_tunnel(instance_id)
    return {"status": "closed"}

@router.post("/search")
async def search_gpus(req: GPUSearchRequest):
    """Search for available GPU offers."""
    offers = await vast_service.search_gpus(
        gpu_name=req.gpu_type,
        min_gpu_ram=req.min_gpu_ram,
        max_price=req.max_price
    )
    # Sort by price
    sorted_offers = sorted(offers, key=lambda x: x.get("dph_total", 999))
    return {
        "count": len(sorted_offers),
        "offers": sorted_offers[:20]  # Limit to top 20
    }

@router.get("/{instance_id}/ssh")
async def get_ssh_info(instance_id: int):
    """Get SSH connection info for an instance."""
    instance = await vast_service.get_instance(instance_id)
    if not instance:
        raise HTTPException(404, "Instance not found")

    return {
        "host": instance.get("ssh_host"),
        "port": instance.get("ssh_port"),
        "command": f"ssh -p {instance.get('ssh_port')} root@{instance.get('ssh_host')}",
        "status": instance.get("cur_state"),
        "jupyter_token": instance.get("jupyter_token")
    }
