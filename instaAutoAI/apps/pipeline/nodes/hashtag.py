"""
Hashtag node – generates relevant hashtags using LLM or rule-based.
"""

import logging
from typing import List, Dict, Any
from ..state import PipelineState
from ..llm_client import LLMClient
from .base import node, RateLimiter

logger = logging.getLogger(__name__)


async def _generate_hashtags(state: PipelineState) -> List[str]:
    """Generate hashtags based on topic and strategy."""
    request = state.get("request_data", {})
    topic = request.get("topic", "")
    niche = request.get("niche", "")
    hashtag_count = request.get("hashtag_count", 20)
    brand_keywords = request.get("brand_keywords", [])

    prompt = f"""
    Generate {hashtag_count} relevant hashtags for a social media post about "{topic}" in the "{niche}" niche.
    Include these brand keywords: {', '.join(brand_keywords) if brand_keywords else 'none'}.
    Return a list of hashtags without the '#' symbol.
    """
    system = "You are a social media hashtag specialist."

    llm = LLMClient.get_client()
    response = await llm.generate_structured(
        prompt,
        response_model=List[str],
        system_prompt=system,
        temperature=0.7,
    )
    # Ensure each starts with #
    return [f"#{tag}" if not tag.startswith("#") else tag for tag in response]


@node(rate_limiter=RateLimiter(max_concurrent=10))
async def hashtag_node(state: PipelineState) -> dict:
    """Hashtag node: generates hashtags."""
    # Idempotency: skip if hashtags already exist and are non-empty
    existing_hashtags = state.get("hashtags")
    if existing_hashtags:
        return {"hashtags": existing_hashtags, "progress": 80, "current_node": "hashtag"}
        
    hashtags = await _generate_hashtags(state)
    return {"hashtags": hashtags, "progress": 80, "current_node": "hashtag"}