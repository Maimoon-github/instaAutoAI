"""
Video generation node – uses FFmpeg to compose video from images and audio,
or calls Replicate video model.
"""

import asyncio
import logging
import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..state import PipelineState
from ..vram_manager import VRAMManager
from .base import node, RateLimiter

logger = logging.getLogger(__name__)


async def _run_ffmpeg(args: List[str]) -> bytes:
    """Run FFmpeg subprocess and return stdout on success."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.error("FFmpeg error: %s", stderr.decode())
        raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")
    return stdout


async def _compose_video(images: List[str], output_path: str, duration: int = 5) -> str:
    """Stitch images into a video using FFmpeg."""
    # Create a temporary file listing images
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for img_path in images:
            f.write(f"file '{img_path}'\n")
        list_file = f.name

    args = [
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        "-y",
        output_path
    ]
    await _run_ffmpeg(args)
    os.unlink(list_file)
    return output_path


@node(rate_limiter=RateLimiter(max_concurrent=1))
async def video_gen_node(state: PipelineState) -> dict:
    """
    Video generation node: composes video from generated images using FFmpeg.
    If no video prompts exist, does nothing.
    """
    # Idempotency check
    existing_videos = state.get("videos")
    if existing_videos:
        return {"videos": existing_videos, "progress": 60, "current_node": "video_gen"}
        
    prompts = state.get("prompts", [])
    video_prompts = [p for p in prompts if p.get("type") == "video"]
    
    if not video_prompts:
        # Check if video content was requested
        strategy = state.get("strategy", {})
        content_mix = strategy.get("suggested_content_mix", [])
        
        if "video" in content_mix:
            # Video was requested but no video prompts - this might be an issue
            # But for now, just return empty
            pass
            
        return {"videos": [], "progress": 60, "current_node": "video_gen"}

    # For simplicity, we'll just generate a placeholder video using FFmpeg from images
    # In practice, call Replicate video model here.
    images = state.get("images", [])
    if not images:
        return {"error": "No images available for video composition", "progress": -1}

    # Create temporary output file
    output_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    try:
        video_url = await _compose_video(images, output_path)
        # For production, upload to cloud storage and return URL
        return {"videos": [output_path], "progress": 60, "current_node": "video_gen"}
    except Exception as e:
        logger.exception("Video composition failed: %s", e)
        return {"error": f"Video generation failed: {e}", "progress": -1}