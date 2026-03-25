"""
LangGraph state management with TypedDict, reducers, and Redis checkpointing.
"""

from typing import Annotated, Any, Dict, List, Optional
from datetime import datetime
from langgraph.graph.message import add_messages
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.redis import RedisSaver
from typing_extensions import TypedDict
import json
import logging
from django.conf import settings
from redis import Redis

logger = logging.getLogger(__name__)


class PipelineState(TypedDict):
    """
    LangGraph state schema for the content generation pipeline.

    Fields:
        messages: List of conversation messages (with add_messages reducer).
        current_node: Name of the node currently executing.
        progress: Integer 0–100 completion percentage.
        result: Accumulated output from agents (merged via custom reducer).
        error: Optional error message.
        timestamp: ISO-format timestamp of last update.
    """
    messages: Annotated[list, add_messages]
    current_node: str
    progress: int
    result: Dict[str, Any]
    error: Optional[str]
    timestamp: str


def merge_result(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Reducer for merging result dictionaries."""
    return {**a, **b}


class StateReducer:
    """Custom reducers for LangGraph state updates."""
    @staticmethod
    def add_messages(messages: list, new_messages: list) -> list:
        """Use LangGraph's built-in add_messages reducer."""
        return add_messages(messages, new_messages)

    @staticmethod
    def merge_result(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two result dictionaries."""
        return merge_result(a, b)


class CheckpointManager:
    """
    Manages checkpoint persistence using Redis (LangGraph RedisSaver).
    Provides methods to save, load, and clean up checkpoints.
    """
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.client = Redis.from_url(self.redis_url)
        self.saver = RedisSaver(self.client)
        self.saver.setup()  # initializes Redis keyspaces

    async def save(self, thread_id: str, state: PipelineState, checkpoint_id: Optional[str] = None):
        """
        Save a checkpoint for the given thread_id.

        :param thread_id: LangGraph thread identifier (typically job_id).
        :param state: Current pipeline state.
        :param checkpoint_id: Optional checkpoint ID; generates new if not provided.
        """
        # Use RedisSaver's async put method (LangGraph >=0.3)
        await self.saver.aput(
            config={"configurable": {"thread_id": thread_id}},
            checkpoint={"state": state, "checkpoint_id": checkpoint_id},
        )
        logger.debug("Saved checkpoint for thread %s", thread_id)

    async def load(self, thread_id: str) -> Optional[PipelineState]:
        """
        Load the latest checkpoint for a thread.
        Returns None if no checkpoint exists.
        """
        config = {"configurable": {"thread_id": thread_id}}
        checkpoint_tuple = await self.saver.aget(config)
        if checkpoint_tuple:
            return checkpoint_tuple[0].get("state")
        return None

    async def delete(self, thread_id: str):
        """Delete all checkpoints for a thread (cleanup after job completion)."""
        # RedisSaver doesn't expose a direct delete; we'll use Redis keys.
        pattern = f"langgraph:checkpoint:{thread_id}:*"
        keys = self.client.keys(pattern)
        if keys:
            self.client.delete(*keys)
            logger.info("Deleted %d checkpoints for thread %s", len(keys), thread_id)