"""
Image generation node – uses Replicate API to generate images from prompts.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
import replicate

from ..state import PipelineState
from ..vram_manager import VRAMManager
from .base import node, RateLimiter, retry_async

logger = logging.getLogger(__name__)


async def _generate_image(prompt: str, aspect_ratio: str) -> Optional[str]:
    """Generate a single image via Replicate."""
    # Map aspect ratio to Replicate model inputs
    model = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
    input = {
        "prompt": prompt,
        "width": 1024,
        "height": 1024,
        "num_outputs": 1,
    }
    if aspect_ratio == "4:5":
        input.update({"width": 896, "height": 1152})
    elif aspect_ratio == "9:16":
        input.update({"width": 768, "height": 1344})

    # Use async Replicate API (requires replicate 1.0+)
    prediction = await replicate.predictions.async_create(
        model=model,
        input=input,
    )
    # Wait for completion (polling)
    while prediction.status not in ("succeeded", "failed", "canceled"):
        await asyncio.sleep(1)
        prediction = await replicate.predictions.async_get(prediction.id)

    if prediction.status == "succeeded":
        return prediction.output[0]  # URL of generated image
    else:
        logger.error("Image generation failed: %s", prediction.error)
        return None


@retry_async(attempts=3, min_wait=2.0, max_wait=30.0)
async def _generate_images(prompts: List[Dict]) -> List[str]:
    """Generate images for all prompts with concurrency control."""
    # Use semaphore to limit concurrent Replicate calls (max 5)
    semaphore = asyncio.Semaphore(5)
    tasks = []
    async def generate_one(prompt_dict):
        async with semaphore:
            return await _generate_image(prompt_dict["prompt"], prompt_dict.get("aspect_ratio", "4:5"))
    for p in prompts:
        if p["type"] == "image":
            tasks.append(generate_one(p))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Filter out errors
    images = [r for r in results if isinstance(r, str) and r is not None]
    return images


@node(rate_limiter=RateLimiter(max_concurrent=1))
async def image_gen_node(state: PipelineState) -> dict:
    """Image generation node."""
    # Idempotency check
    existing_images = state.get("images")
    if existing_images:
        return {"images": existing_images, "progress": 50, "current_node": "image_gen"}
        
    prompts = state.get("prompts", [])
    
    # If no prompts, check if visual content was actually requested
    if not prompts:
        strategy = state.get("strategy", {})
        content_mix = strategy.get("suggested_content_mix", ["image"])
        
        # If no visual content requested, skip gracefully
        if not content_mix:
            return {"images": [], "progress": 50, "current_node": "image_gen"}
        else:
            # Visual content was requested but prompts are missing - this is an error
            return {
                "error": "No prompts found for image generation", 
                "progress": -1
            }
    
    # Generate images from prompts...
    vram_mgr = VRAMManager(required_mb=1024)
    async with vram_mgr:
        images = await _generate_images(prompts)

    if images:
        return {"images": images, "progress": 50, "current_node": "image_gen"}
    else:
        return {"error": "All image generations failed", "progress": -1}