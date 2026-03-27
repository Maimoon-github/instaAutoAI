"""
Async pipeline runner with checkpointing support.

Provides methods to run the LangGraph pipeline and stream state updates.
"""

import asyncio
import logging
from typing import AsyncIterator, Dict, Any, Optional
from uuid import UUID

from langgraph.graph import StateGraph

from .graph import get_graph
from .state import PipelineState

from datetime import datetime

logger = logging.getLogger(__name__)


class PipelineRunner:
    """
    Executes the LangGraph pipeline with checkpointing and streaming.
    Each runner is tied to a specific thread (job) and holds a reference
    to the compiled graph.
    """

    def __init__(self, thread_id: UUID):
        self.thread_id = str(thread_id)
        self._graph: Optional[StateGraph] = None
        self._running = False

    async def _ensure_graph(self) -> StateGraph:
        """Lazily load the graph (once per runner)."""
        if self._graph is None:
            self._graph = await get_graph()
        return self._graph

    async def arun(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the pipeline from start (or resume from last checkpoint)
        and return the final state.

        :param initial_state: The initial pipeline state (typically from a job).
        :return: The final state after all nodes have executed.
        """
        graph = await self._ensure_graph()
        config = {"configurable": {"thread_id": self.thread_id}}

        try:
            self._running = True
            final_state = await graph.ainvoke(initial_state, config=config)
            logger.info("Pipeline completed for thread %s", self.thread_id)
            return final_state
        except asyncio.CancelledError:
            logger.info("Pipeline cancelled for thread %s", self.thread_id)
            # Optionally clean up checkpoint or mark job as failed
            raise
        except Exception as e:
            logger.exception("Pipeline failed for thread %s: %s", self.thread_id, e)
            # Mark job as failed in the state (could be done by export node)
            raise
        finally:
            self._running = False

    async def astream(self, initial_state: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream state updates as they happen. Yields the full state after each node.

        :param initial_state: The initial pipeline state.
        :yield: State updates (dictionaries) as they become available.
        """
        graph = await self._ensure_graph()
        config = {"configurable": {"thread_id": self.thread_id}}

        try:
            self._running = True
            async for event in graph.astream(initial_state, config=config):
                # LangGraph yields dicts with node names as keys
                # We'll yield the state update part (the value) for simplicity
                for node, update in event.items():
                    if isinstance(update, dict):
                        yield update
                    else:
                        yield {"__event__": node, "value": update}
        except asyncio.CancelledError:
            logger.info("Stream cancelled for thread %s", self.thread_id)
            raise
        finally:
            self._running = False

    async def cleanup(self) -> None:
        """
        Delete checkpoint data for this thread after job completion.
        """
        # For PostgreSQL/Redis, we need to remove checkpoint entries.
        # Since LangGraph does not expose a delete method, we can manually
        # delete from the underlying storage. This is optional.
        # We'll rely on the checkpointer to auto-expire or ignore.
        # For now, just a placeholder.
        logger.info("Cleanup for thread %s – no automatic checkpoint deletion", self.thread_id)


async def run_pipeline(job_id: str, request_data: dict) -> dict:
    """
    Entry point for the pipeline from Celery task.
    """
    from .state import PipelineState  # avoid circular import

    runner = PipelineRunner(thread_id=UUID(job_id))
    initial_state: PipelineState = {
        "job_id": job_id,
        "request_data": request_data,
        "messages": [],
        "current_node": "",
        "progress": 0,
        "result": {},
        "error": None,
        "timestamp": datetime.utcnow().isoformat(),
        "strategy": {},
        "prompts": [],
        "images": [],
        "videos": [],
        "captions": [],
        "hashtags": [],
        "export_metadata": {},
    }
    final_state = await runner.arun(initial_state)
    return final_state