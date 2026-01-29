from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.instances import router as instances_router
from api.datasets import router as datasets_router
from api.loras import router as loras_router

app = FastAPI(title="LoRA Cloud")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(instances_router)
app.include_router(datasets_router)
app.include_router(loras_router)

@app.get("/health")
def health():
    return {"status": "ok"}
