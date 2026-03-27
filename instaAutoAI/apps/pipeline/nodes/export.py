"""
Export node – final aggregation, uploads assets to storage, returns metadata.
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
from django.conf import settings
from ..state import PipelineState
from .base import node, RateLimiter
import urllib.parse


logger = logging.getLogger(__name__)


async def _upload_file(local_path: str, destination: str) -> str:
    """Upload a file to cloud storage (placeholder)."""
    # Handle URLs differently from local files
    if local_path.startswith(('http://', 'https://')):
        # It's already a URL, just return it (or download then copy if needed)
        logger.info("Skipping upload for existing URL: %s", local_path)
        return local_path
        
    media_root = Path(settings.MEDIA_ROOT)
    dest_path = media_root / destination
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Only copy if it's a local file path
    if os.path.isfile(local_path):
        await asyncio.to_thread(shutil.copy2, local_path, dest_path)
    else:
        logger.warning("Source file not found: %s", local_path)
        return local_path  # Return original if can't copy
        
    return settings.MEDIA_URL + destination


async def _export_assets(state: PipelineState) -> Dict[str, Any]:
    """Compile and upload all assets."""
    job_id = state.get("job_id", "unknown")
    images = state.get("images", [])
    videos = state.get("videos", [])
    captions = state.get("captions", [])
    hashtags = state.get("hashtags", [])

    exported = {}
    upload_errors = []

    # Upload images
    image_urls = []
    for idx, img_path in enumerate(images):
        try:
            dest = f"jobs/{job_id}/image_{idx}.png"
            url = await _upload_file(img_path, dest)
            image_urls.append(url)
            # Clean up local file only if it's a local path
            if os.path.isfile(img_path):
                await asyncio.to_thread(os.unlink, img_path)
        except Exception as e:
            logger.error("Failed to export image %s: %s", img_path, e)
            upload_errors.append(f"Image {idx}: {e}")
    exported["image_urls"] = image_urls

    # Upload videos
    video_urls = []
    for idx, vid_path in enumerate(videos):
        try:
            dest = f"jobs/{job_id}/video_{idx}.mp4"
            url = await _upload_file(vid_path, dest)
            video_urls.append(url)
            if os.path.isfile(vid_path):
                await asyncio.to_thread(os.unlink, vid_path)
        except Exception as e:
            logger.error("Failed to export video %s: %s", vid_path, e)
            upload_errors.append(f"Video {idx}: {e}")
    exported["video_urls"] = video_urls

    exported["captions"] = captions
    exported["hashtags"] = hashtags
    exported["job_id"] = job_id
    
    # Raise if any uploads failed
    if upload_errors:
        raise Exception(f"Upload failures: {'; '.join(upload_errors)}")
    
    return exported


@node(rate_limiter=RateLimiter(max_concurrent=5))
async def export_node(state: PipelineState) -> dict:
    """
    Export node: aggregates all generated content, uploads to storage,
    and returns final metadata.
    """
    # Propagate errors from previous nodes immediately
    if state.get("error"):
        return {
            "export_metadata": {},
            "progress": -1,
            "current_node": "export",
            "error": state["error"],
        }
    
    try:
        metadata = await _export_assets(state)
        
        # Check if any exports actually failed (URLs unchanged indicate failure)
        failed_uploads = []
        for url in metadata.get("image_urls", []):
            if url.startswith("http://") or url.startswith("https://"):
                continue  # These are fine
            # If it's a local path, the upload didn't convert to URL
            if os.path.exists(url) or ":" in url:  # Windows path check
                failed_uploads.append(url)
        
        # Alternative: Check if upload actually succeeded by seeing if we got URLs back
        # Actually, let's modify _export_assets to track failures instead
        
        return {
            "export_metadata": metadata,
            "progress": 100,
            "current_node": "export",
            "result": metadata,
        }
    except Exception as e:
        logger.exception("Export failed: %s", e)
        return {
            "error": f"Export failed: {e}", 
            "progress": -1,
            "current_node": "export",
            "export_metadata": {},
        }