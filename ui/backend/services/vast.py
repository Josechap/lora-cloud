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
