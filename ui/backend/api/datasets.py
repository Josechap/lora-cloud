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

@router.get("/{name}")
def get_dataset(name: str):
    """Get dataset details with file list."""
    files = gcs_service.get_dataset_files(name)
    if not files:
        raise HTTPException(404, "Dataset not found")
    return {
        "name": name,
        "files": files,
        "file_count": len(files),
        "total_size": sum(f["size"] for f in files)
    }

@router.get("/{name}/files/{filename}/url")
def get_file_url(name: str, filename: str):
    """Get a signed URL to download a file."""
    remote_path = f"datasets/{name}/{filename}"
    try:
        url = gcs_service.get_signed_url(remote_path)
        return {"url": url}
    except Exception as e:
        raise HTTPException(404, f"File not found: {e}")

@router.delete("/{name}")
def delete_dataset(name: str):
    """Delete a dataset."""
    blobs = list(gcs_service.bucket.list_blobs(prefix=f"datasets/{name}/"))
    if not blobs:
        raise HTTPException(404, "Dataset not found")
    for blob in blobs:
        blob.delete()
    return {"status": "deleted"}

@router.delete("/{name}/files/{filename}")
def delete_file(name: str, filename: str):
    """Delete a single file from a dataset."""
    remote_path = f"datasets/{name}/{filename}"
    try:
        gcs_service.delete_file(remote_path)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(404, f"File not found: {e}")
