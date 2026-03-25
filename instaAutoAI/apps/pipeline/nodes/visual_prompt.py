"""
Visual prompt node – transforms strategy into image/video generation prompts.
"""

import logging
from typing import List, Dict, Any
from ..state import PipelineState
from ..llm_client import LLMClient
from .base import node, RateLimiter

logger = logging.getLogger(__name__)


async def _generate_prompts(state: PipelineState) -> List[Dict[str, Any]]:
    """Generate prompts for each content piece."""
    strategy = state.get("strategy", {})
    content_mix = strategy.get("suggested_content_mix", ["image"])
    visual_style = strategy.get("visual_style", "realistic")
    aspect_ratio = state.get("request_data", {}).get("aspect_ratio", "4:5")

    prompts = []
    for item in content_mix:
        if item == "image":
            prompt_text = f"Generate a prompt for an image about {strategy.get('primary_message', 'the topic')} in {visual_style} style. Aspect ratio: {aspect_ratio}."
        elif item == "video":
            prompt_text = f"Generate a prompt for a short video clip about {strategy.get('primary_message', 'the topic')} in {visual_style} style."
        else:
            continue

        llm = LLMClient.get_client()
        response = await llm.generate(prompt_text, temperature=0.8, max_tokens=200)
        prompts.append({
            "type": item,
            "prompt": response.strip(),
            "aspect_ratio": aspect_ratio,
            "style": visual_style,
        })
    return prompts


@node(rate_limiter=RateLimiter(max_concurrent=10))
async def visual_prompt_node(state: PipelineState) -> dict:
    """
    Visual prompt node: generates prompts for each piece of content.
    Returns state updates: 'prompts' list (will be appended via reducer).
    """
    new_prompts = await _generate_prompts(state)
    return {"prompts": new_prompts, "progress": 20, "current_node": "visual_prompt"}