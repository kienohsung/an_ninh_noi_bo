# File path: security_mgmt_v2_3_local/backend/app/routers/gcp.py
import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from google.cloud import storage

from ..config import settings
from ..auth import get_current_user

router = APIRouter(prefix="/gcp", tags=["gcp"])

@router.post("/generate-upload-url", response_model=dict)
def generate_upload_url(
    filename: str,
    content_type: str,
    user: dict = Depends(get_current_user)
):
    """
    Tạo một Signed URL để cho phép frontend tải file trực tiếp lên Google Cloud Storage.
    """
    if not settings.GCS_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="Google Cloud Storage bucket name is not configured.")

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)

        # Tạo một tên file duy nhất để tránh trùng lặp
        unique_filename = f"uploads/{uuid.uuid4()}-{filename}"
        
        blob = bucket.blob(unique_filename)

        # Tạo URL có hiệu lực trong 15 phút
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="PUT",
            content_type=content_type,
        )
        return {"upload_url": url, "gcs_path": unique_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate upload URL: {e}")

