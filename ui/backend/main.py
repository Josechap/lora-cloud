from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.instances import router as instances_router
from api.datasets import router as datasets_router
from api.loras import router as loras_router
from api.training import router as training_router
from config import settings

app = FastAPI(
    title="LoRA Cloud",
    version="1.0.0",
    description="Train Flux LoRAs on vast.ai with a local web UI"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(instances_router, prefix="/api")
app.include_router(datasets_router, prefix="/api")
app.include_router(loras_router, prefix="/api")
app.include_router(training_router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/status")
def status():
    """Get system configuration status."""
    return {
        "vast_configured": settings.is_vast_configured,
        "gcs_configured": settings.is_gcs_configured,
        "gcs_bucket": settings.gcs_bucket if settings.is_gcs_configured else None,
        "defaults": {
            "gpu_type": settings.default_gpu_type,
            "max_price": settings.default_max_price,
            "disk_gb": settings.default_disk_gb
        }
    }
