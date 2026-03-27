"""
LangGraph state management with TypedDict, reducers, and Redis checkpointing.
"""

# from typing import Annotated, Any, Dict, Optional
from typing import Annotated, Any, Dict, List, Optional
from datetime import datetime
from langgraph.graph.message import add_messages
from langgraph.checkpoint.base import BaseCheckpointSaver
from typing_extensions import TypedDict
import logging
from django.conf import settings
import redis

logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    """
    LangGraph state schema for the content generation pipeline.
    """
    messages: Annotated[list, add_messages]
    current_node: str
    progress: int
    result: Dict[str, Any]
    error: Optional[str]
    timestamp: str
    # Add these missing keys used by nodes:
    job_id: Optional[str]
    request_data: Optional[Dict[str, Any]]
    strategy: Optional[Dict[str, Any]]
    # prompts: Optional[List[Dict[str, Any]]]
    # images: Optional[List[str]]
    prompts: Optional[list[Dict[str, Any]]]
    images: Optional[list[str]]
    videos: Optional[List[str]]
    captions: Optional[List[str]]
    hashtags: Optional[List[str]]
    export_metadata: Optional[Dict[str, Any]]



def merge_result(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer for merging result dictionaries."""
    return {**a, **b}


class StateReducer:
    """Custom reducers for LangGraph state updates."""
    @staticmethod
    def add_messages(messages: list, new_messages: list) -> list:
        return add_messages(messages, new_messages)

    @staticmethod
    def merge_result(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        return merge_result(a, b)


class CheckpointManager:
    """
    Manages checkpoint persistence using Redis (if available), otherwise in‑memory.
    """
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._saver = None
        self._client = None

    @property
    def saver(self):
        if self._saver is None:
            try:
                from langgraph.checkpoint.redis import AsyncRedisSaver
                from redis.asyncio import Redis as AsyncRedis
                self._client = AsyncRedis.from_url(self.redis_url)
                self._saver = AsyncRedisSaver(self._client)
                # Note: asetup() is async; we'll call it lazily
                logger.info("Using Redis checkpointer")
            except ImportError:
                # Fallback to in‑memory
                from langgraph.checkpoint.memory import AsyncMemorySaver
                self._saver = AsyncMemorySaver()
                logger.warning("Redis checkpointer not available; using in‑memory AsyncMemorySaver")
        return self._saver

    async def _ensure_setup(self):
        if hasattr(self.saver, 'asetup') and not getattr(self, '_setup_done', False):
            await self.saver.asetup()
            self._setup_done = True

    async def save(self, thread_id: str, state: PipelineState, checkpoint_id: Optional[str] = None):
        await self._ensure_setup()
        await self.saver.aput(
            config={"configurable": {"thread_id": thread_id}},
            checkpoint={"state": state, "checkpoint_id": checkpoint_id},
        )
        logger.debug("Saved checkpoint for thread %s", thread_id)

    async def load(self, thread_id: str) -> Optional[PipelineState]:
        await self._ensure_setup()
        config = {"configurable": {"thread_id": thread_id}}
        checkpoint_tuple = await self.saver.aget(config)
        if checkpoint_tuple:
            return checkpoint_tuple[0].get("state")
        return None

    async def delete(self, thread_id: str):
        # Redis deletion is not supported by the generic saver; fallback to direct Redis if available
        if self._client:
            pattern = f"langgraph:checkpoint:{thread_id}:*"
            keys = await self._client.keys(pattern)
            if keys:
                await self._client.delete(*keys)
                logger.info("Deleted %d checkpoints for thread %s", len(keys), thread_id)
        else:
            logger.debug("Checkpoint deletion not implemented for in‑memory saver")