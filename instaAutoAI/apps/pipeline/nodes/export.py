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

logger = logging.getLogger(__name__)


async def _upload_file(local_path: str, destination: str) -> str:
    """Upload a file to cloud storage (placeholder)."""
    # In production, use boto3 or django-storages
    # For now, copy to media directory
    media_root = Path(settings.MEDIA_ROOT)
    dest_path = media_root / destination
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(shutil.copy2, local_path, dest_path)
    # Return public URL
    return settings.MEDIA_URL + destination


async def _export_assets(state: PipelineState) -> Dict[str, Any]:
    """Compile and upload all assets."""
    job_id = state.get("job_id")
    images = state.get("images", [])
    videos = state.get("videos", [])
    captions = state.get("captions", [])
    hashtags = state.get("hashtags", [])

    exported = {}

    # Upload images
    image_urls = []
    for idx, img_path in enumerate(images):
        dest = f"jobs/{job_id}/image_{idx}.png"
        url = await _upload_file(img_path, dest)
        image_urls.append(url)
        # Clean up local file
        await asyncio.to_thread(os.unlink, img_path)
    exported["image_urls"] = image_urls

    # Upload videos
    video_urls = []
    for idx, vid_path in enumerate(videos):
        dest = f"jobs/{job_id}/video_{idx}.mp4"
        url = await _upload_file(vid_path, dest)
        video_urls.append(url)
        await asyncio.to_thread(os.unlink, vid_path)
    exported["video_urls"] = video_urls

    exported["captions"] = captions
    exported["hashtags"] = hashtags
    exported["job_id"] = job_id
    return exported


@node(rate_limiter=RateLimiter(max_concurrent=5))
async def export_node(state: PipelineState) -> dict:
    """
    Export node: aggregates all generated content, uploads to storage,
    and returns final metadata.
    """
    try:
        metadata = await _export_assets(state)
        return {
            "export_metadata": metadata,
            "progress": 100,
            "current_node": "export",
            "result": metadata,  # Also store in result field
        }
    except Exception as e:
        logger.exception("Export failed: %s", e)
        return {"error": f"Export failed: {e}", "progress": -1}