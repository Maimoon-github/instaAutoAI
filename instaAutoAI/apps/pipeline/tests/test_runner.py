"""
Tests for PipelineRunner with mocked graph.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import asyncio
from uuid import uuid4

from apps.pipeline.runner import PipelineRunner


pytestmark = pytest.mark.asyncio


class TestPipelineRunner:
    @pytest.fixture
    def mock_graph(self, monkeypatch):
        """Mock get_graph to return a controllable async graph."""
        mock_graph = AsyncMock()
        mock_graph.ainvoke = AsyncMock(return_value={"progress": 100, "result": "done"})
        
        # FIX: Don't use AsyncMock for astream - use a regular Mock with side_effect 
        # that returns an async generator function result
        async def astream_gen(*a, **kw):
            yield {"node1": {"progress": 10}}
            yield {"node2": {"progress": 50}}
        
        # Assign the async generator function directly as side_effect
        # mock_graph.astream = mock.Mock(side_effect=astream_gen)
        mock_graph.astream = Mock(side_effect=astream_gen)
        
        monkeypatch.setattr("apps.pipeline.runner.get_graph", AsyncMock(return_value=mock_graph))
        return mock_graph 



    async def test_arun_success(self, mock_graph):
        """Should run pipeline and return final state."""
        thread_id = uuid4()
        runner = PipelineRunner(thread_id)
        initial_state = {"job_id": str(thread_id)}
        result = await runner.arun(initial_state)
        assert result["progress"] == 100
        mock_graph.ainvoke.assert_called_once_with(initial_state, config={"configurable": {"thread_id": str(thread_id)}})

    async def test_arun_handles_cancellation(self, mock_graph):
        """Should handle CancelledError gracefully."""
        thread_id = uuid4()
        runner = PipelineRunner(thread_id)
        mock_graph.ainvoke.side_effect = asyncio.CancelledError
        initial_state = {}
        with pytest.raises(asyncio.CancelledError):
            await runner.arun(initial_state)
        # Optionally verify cleanup logs, but not implemented

    async def test_arun_handles_exception(self, mock_graph):
        """Should propagate exceptions."""
        thread_id = uuid4()
        runner = PipelineRunner(thread_id)
        mock_graph.ainvoke.side_effect = Exception("Graph failure")
        initial_state = {}
        with pytest.raises(Exception, match="Graph failure"):
            await runner.arun(initial_state)

    async def test_astream_yields_updates(self, mock_graph):
        """Should yield state updates as they come."""
        thread_id = uuid4()
        runner = PipelineRunner(thread_id)
        initial_state = {}
        updates = []
        async for update in runner.astream(initial_state):
            updates.append(update)
        assert len(updates) == 2
        assert updates[0]["progress"] == 10
        assert updates[1]["progress"] == 50


    async def test_astream_handles_cancellation(self, mock_graph):
        """Should handle cancellation during streaming."""
        async def astream_gen_cancel(*a, **kw):
            yield {"node1": {"progress": 10}}
            raise asyncio.CancelledError()
        
        # FIX: Use mock.Mock instead of AsyncMock for astream
        mock_graph.astream = Mock(side_effect=astream_gen_cancel)
        
        thread_id = uuid4()
        runner = PipelineRunner(thread_id)
        initial_state = {}
        with pytest.raises(asyncio.CancelledError):
            async for _ in runner.astream(initial_state):
                pass


    async def test_cleanup(self, caplog): 
        """Cleanup should log but not raise."""
        thread_id = uuid4()
        runner = PipelineRunner(thread_id)
        await runner.cleanup()
        assert "Cleanup for thread" in caplog.text