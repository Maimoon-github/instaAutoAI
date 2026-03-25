"""
LangGraph state graph builder with checkpointing support.

Uses nodes from the `nodes` package and compiles the graph with
an async checkpointer (PostgreSQL or Redis). The graph is built
lazily and cached.
"""

import logging
from typing import Optional

from langgraph.graph import StateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres import AsyncPostgresSaver
from langgraph.checkpoint.redis import AsyncRedisSaver
from psycopg_pool import AsyncConnectionPool
from redis.asyncio import Redis

from .state import PipelineState
from .nodes import (
    strategy_node,
    visual_prompt_node,
    image_gen_node,
    video_gen_node,
    caption_node,
    hashtag_node,
    export_node,
)

logger = logging.getLogger(__name__)

_graph_cache = None
_checkpointer_cache = None


async def get_checkpointer() -> BaseCheckpointSaver:
    """
    Return an async checkpointer (PostgreSQL or Redis) based on settings.
    The checkpointer is cached to avoid reinitialisation.
    """
    global _checkpointer_cache
    if _checkpointer_cache is not None:
        return _checkpointer_cache

    from django.conf import settings

    # Determine which checkpointer to use
    if hasattr(settings, "LANGGRAPH_CHECKPOINT_REDIS_URL"):
        # Use Redis
        redis_client = Redis.from_url(settings.LANGGRAPH_CHECKPOINT_REDIS_URL)
        _checkpointer_cache = AsyncRedisSaver(redis_client)
        await _checkpointer_cache.asetup()
        logger.info("LangGraph using Redis checkpointer")
    elif hasattr(settings, "LANGGRAPH_CHECKPOINT_DB_URL"):
        # Use PostgreSQL
        pool = AsyncConnectionPool(settings.LANGGRAPH_CHECKPOINT_DB_URL)
        _checkpointer_cache = AsyncPostgresSaver(pool)
        await _checkpointer_cache.setup()
        logger.info("LangGraph using PostgreSQL checkpointer")
    else:
        # Fallback to in-memory (development only)
        from langgraph.checkpoint.memory import MemorySaver
        _checkpointer_cache = MemorySaver()
        logger.warning("No checkpoint DB configured – using in-memory storage")

    return _checkpointer_cache


def build_graph(checkpointer: Optional[BaseCheckpointSaver] = None) -> StateGraph:
    """
    Build and return a compiled StateGraph with all nodes and edges.
    If a checkpointer is provided, the graph is compiled with it.
    """
    # Define the graph with the state schema
    workflow = StateGraph(PipelineState)

    # Add all nodes
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("visual_prompt", visual_prompt_node)
    workflow.add_node("image_gen", image_gen_node)
    workflow.add_node("video_gen", video_gen_node)
    workflow.add_node("caption", caption_node)
    workflow.add_node("hashtag", hashtag_node)
    workflow.add_node("export", export_node)

    # Define the edges (simple linear flow)
    workflow.set_entry_point("strategy")
    workflow.add_edge("strategy", "visual_prompt")
    workflow.add_edge("visual_prompt", "image_gen")
    workflow.add_edge("image_gen", "video_gen")
    workflow.add_edge("video_gen", "caption")
    workflow.add_edge("caption", "hashtag")
    workflow.add_edge("hashtag", "export")

    # Compile with checkpointer if provided
    if checkpointer:
        graph = workflow.compile(checkpointer=checkpointer)
        logger.info("Graph compiled with checkpointer")
    else:
        graph = workflow.compile()
        logger.info("Graph compiled without checkpointer (development)")

    return graph


async def get_graph() -> StateGraph:
    """
    Return a compiled graph with a checkpointer (lazy initialization).
    The graph is cached after first build.
    """
    global _graph_cache
    if _graph_cache is None:
        checkpointer = await get_checkpointer()
        _graph_cache = build_graph(checkpointer)
    return _graph_cache