from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    vast_api_key: str = ""
    gcs_bucket: str = ""
    gcs_credentials_path: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
