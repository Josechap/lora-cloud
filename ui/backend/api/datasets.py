from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from services.gcs import gcs_service
import tempfile
import os

router = APIRouter(prefix="/datasets", tags=["datasets"])

@router.get("")
def list_datasets():
    """List all datasets."""
    return gcs_service.list_datasets()

@router.post("/{name}/upload")
async def upload_images(name: str, files: list[UploadFile] = File(...)):
    """Upload images to a dataset."""
    uploaded = []
    for file in files:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp.flush()

            remote_path = f"datasets/{name}/{file.filename}"
            gcs_service.upload_file(tmp.name, remote_path)
            uploaded.append(remote_path)
            os.unlink(tmp.name)

    return {"uploaded": uploaded}

@router.delete("/{name}")
def delete_dataset(name: str):
    """Delete a dataset."""
    blobs = gcs_service.bucket.list_blobs(prefix=f"datasets/{name}/")
    for blob in blobs:
        blob.delete()
    return {"status": "deleted"}
