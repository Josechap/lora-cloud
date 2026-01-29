from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    vast_api_key: str = ""
    gcs_bucket: str = ""
    gcs_credentials_path: str = ""

    # Optional settings with defaults
    default_gpu_type: str = "RTX 4090"
    default_max_price: float = 0.6
    default_disk_gb: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def is_vast_configured(self) -> bool:
        return bool(self.vast_api_key)

    @property
    def is_gcs_configured(self) -> bool:
        return bool(self.gcs_bucket and self.gcs_credentials_path and
                    os.path.exists(self.gcs_credentials_path))

settings = Settings()
