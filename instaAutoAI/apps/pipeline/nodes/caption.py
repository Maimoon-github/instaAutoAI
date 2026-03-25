"""
Caption node – generates captions using LLM with tone and length parameters.
"""

import logging
from typing import List, Dict, Any
from ..state import PipelineState
from ..llm_client import LLMClient
from .base import node, RateLimiter

logger = logging.getLogger(__name__)


async def _generate_captions(state: PipelineState) -> List[str]:
    """Generate multiple caption variations."""
    request = state.get("request_data", {})
    strategy = state.get("strategy", {})
    topic = request.get("topic", "")
    tone = request.get("tone", "professional")
    caption_length = request.get("caption_length", "medium")
    primary_message = strategy.get("primary_message", topic)

    length_map = {"short": 100, "medium": 300, "long": 600}
    max_chars = length_map.get(caption_length, 300)

    prompt = f"""
    Write a {caption_length} caption (max {max_chars} chars) for a social media post about "{topic}".
    Primary message: {primary_message}. Tone: {tone}.
    The caption should be engaging and include a call to action.
    Return a list of 3 different variations.
    """
    system = "You are a creative copywriter for social media."

    llm = LLMClient.get_client()
    # For simplicity, we'll ask for JSON list
    response = await llm.generate_structured(
        prompt,
        response_model=List[str],
        system_prompt=system,
        temperature=0.8,
    )
    return response


@node(rate_limiter=RateLimiter(max_concurrent=10))
async def caption_node(state: PipelineState) -> dict:
    """
    Caption node: generates caption variations.
    Returns state updates: 'captions' list (appended via reducer).
    """
    captions = await _generate_captions(state)
    return {"captions": captions, "progress": 70, "current_node": "caption"}