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
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(
                f"{VAST_API_URL}/bundles/",
                headers=self.headers
            )
            resp.raise_for_status()
            offers = resp.json().get("offers", [])
            # Filter offers in Python - only rentable ones
            filtered = [
                o for o in offers
                if gpu_name.lower() in o.get("gpu_name", "").lower()
                and o.get("gpu_ram", 0) >= min_gpu_ram
                and o.get("dph_total", 999) <= max_price
                and o.get("rentable", False) == True
            ]
            return filtered

    async def rent_instance(
        self,
        offer_id: int,
        image: str,
        disk_gb: int = 50
    ) -> dict:
        """Rent a GPU instance."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            resp = await client.put(
                f"{VAST_API_URL}/asks/{offer_id}/",
                headers=self.headers,
                json={
                    "image": image,
                    "disk": disk_gb,
                    "runtype": "ssh"
                }
            )
            if resp.status_code != 200:
                error_data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {"msg": resp.text}
                raise Exception(f"Vast.ai error: {error_data.get('msg', resp.text)}")
            return resp.json()

    async def get_instances(self) -> list[dict]:
        """Get all running instances."""
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(
                f"{VAST_API_URL}/instances/",
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
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.delete(
                f"{VAST_API_URL}/instances/{instance_id}/",
                headers=self.headers
            )
            return resp.status_code == 200

vast_service = VastService()
