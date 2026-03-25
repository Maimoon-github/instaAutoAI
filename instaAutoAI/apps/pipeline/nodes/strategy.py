"""
Content strategy node – generates a structured plan using LLM.
"""

import logging
from typing import Dict, Any
from langgraph.types import Command

from ..state import PipelineState
from ..llm_client import LLMClient
from .base import node, RateLimiter

logger = logging.getLogger(__name__)


async def _generate_strategy(state: PipelineState) -> Dict[str, Any]:
    """Core logic to generate strategy from state parameters."""
    # Extract parameters from request_data or result
    request = state.get("request_data", {})
    topic = request.get("topic", "")
    niche = request.get("niche", "")
    tone = request.get("tone", "professional")
    output_format = request.get("output_format", "image")

    # Build prompt for LLM
    prompt = f"""
    Generate a content strategy for a social media post about "{topic}" in the "{niche}" niche.
    Tone: {tone}. Output format: {output_format}.
    Return a JSON object with:
    - primary_message: str
    - visual_style: str
    - suggested_content_mix: list of strings (e.g., ["image", "video"])
    - target_platforms: list of str
    - estimated_complexity: "low", "medium", "high"
    """
    system = "You are a creative strategist for social media content."

    llm = LLMClient.get_client()
    response = await llm.generate_structured(
        prompt,
        response_model=Dict,  # In practice, use a Pydantic model
        system_prompt=system,
        temperature=0.7,
    )
    # Parse response (assuming it's already dict)
    strategy = response if isinstance(response, dict) else {"raw": response}
    return {"strategy": strategy, "progress": 10, "current_node": "strategy"}


@node(rate_limiter=RateLimiter(max_concurrent=10))  # LLM calls limited to 10 concurrent
async def strategy_node(state: PipelineState) -> dict:
    """
    Strategy node: uses LLM to generate content strategy.
    Returns state updates including 'strategy' and progress.
    """
    # Optional: use Command for conditional routing based on strategy
    result = await _generate_strategy(state)
    # If complexity is high, maybe branch to additional analysis
    # return Command(goto="special_node", update=result)
    return result