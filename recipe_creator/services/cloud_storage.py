"""Cloud storage service for recipe images - supports GCS or local fallback."""

import os
import base64
from datetime import timedelta
from pathlib import Path
from typing import Optional

from loguru import logger


# Local images directory as fallback
LOCAL_IMAGES_DIR = Path(__file__).parent.parent / "images"


def _ensure_local_dir() -> Path:
    """Ensure local images directory exists."""
    LOCAL_IMAGES_DIR.mkdir(exist_ok=True)
    return LOCAL_IMAGES_DIR


def _has_gcs_credentials() -> bool:
    """Check if GCS credentials are configured."""
    # Check for service account file
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if os.path.exists(creds_path):
            return True
    
    # Check for ADC (gcloud auth application-default login)
    default_adc = Path.home() / ".config" / "gcloud" / "application_default_credentials.json"
    if default_adc.exists():
        return True
    
    return False


def _maybe_generate_signed_url(blob) -> Optional[str]:
    """Generate a time-limited signed URL if credentials permit signing."""
    try:
        return blob.generate_signed_url(
            expiration=timedelta(days=7), method="GET"
        )
    except Exception:
        # Likely using end-user ADC without signing capability; fall back to public URL
        return None


def upload_image(image_data: bytes, recipe_id: str, bucket_name: Optional[str] = None) -> str:
    """
    Upload image to GCS or save locally as fallback.
    
    Args:
        image_data: Raw image bytes
        recipe_id: Recipe UUID for filename
        bucket_name: GCS bucket name. If None, reads from GCS_BUCKET_NAME env var.
        
    Returns:
        URL or local path of the saved image
    """
    bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME")
    
    # Try GCS first if configured
    if bucket_name and _has_gcs_credentials():
        try:
            from google.cloud import storage
            
            # ADC requires explicit project ID
            project = os.getenv("GOOGLE_CLOUD_PROJECT")
            client = storage.Client(project=project)
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(f"recipes/{recipe_id}.png")
            
            blob.upload_from_string(image_data, content_type="image/png")
            
            # Prefer signed URL (works with private buckets when using a service account)
            signed_url = _maybe_generate_signed_url(blob)
            if signed_url:
                logger.success(f"Image uploaded to GCS (signed URL): {signed_url}")
                return signed_url
            
            # Fallback: public URL (requires bucket to allow public reads)
            public_url = f"https://storage.googleapis.com/{bucket_name}/recipes/{recipe_id}.png"
            logger.success(f"Image uploaded to GCS (public URL): {public_url}")
            return public_url
            
        except Exception as e:
            logger.warning(f"GCS upload failed, falling back to local: {e}")
    
    # Fallback: save locally
    return _save_locally(image_data, recipe_id)


def _save_locally(image_data: bytes, recipe_id: str) -> str:
    """Save image to local filesystem."""
    images_dir = _ensure_local_dir()
    filepath = images_dir / f"{recipe_id}.png"
    
    filepath.write_bytes(image_data)
    logger.info(f"Image saved locally: {filepath}")
    
    # Return a file:// URL or relative path
    return f"file://{filepath.absolute()}"


def delete_image(recipe_id: str, bucket_name: Optional[str] = None) -> bool:
    """
    Delete image from GCS or local storage.
    
    Args:
        recipe_id: Recipe UUID for filename
        bucket_name: GCS bucket name. If None, reads from GCS_BUCKET_NAME env var.
        
    Returns:
        True if deletion succeeded, False otherwise
    """
    bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME")
    
    # Try GCS first
    if bucket_name and _has_gcs_credentials():
        try:
            from google.cloud import storage
            
            project = os.getenv("GOOGLE_CLOUD_PROJECT")
            client = storage.Client(project=project)
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(f"recipes/{recipe_id}.png")
            blob.delete()
            logger.info(f"Image deleted from GCS: {recipe_id}")
            return True
        except Exception as e:
            logger.warning(f"GCS delete failed: {e}")
    
    # Try local deletion
    local_path = LOCAL_IMAGES_DIR / f"{recipe_id}.png"
    if local_path.exists():
        local_path.unlink()
        logger.info(f"Image deleted locally: {recipe_id}")
        return True
    
    return False


def get_image_data_url(image_data: bytes) -> str:
    """Convert image bytes to a data URL for inline display."""
    b64 = base64.b64encode(image_data).decode()
    return f"data:image/png;base64,{b64}"
