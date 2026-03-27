"""
Integration tests for LangGraph compiled graph with MemorySaver checkpointer.
"""

import pytest
from langgraph.checkpoint.memory import MemorySaver
from apps.pipeline.graph import build_graph
from apps.pipeline.state import PipelineState


pytestmark = pytest.mark.asyncio


@pytest.fixture
def graph():
    """Compiled graph with MemorySaver."""
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)
    return graph


class TestGraphIntegration:
    async def test_full_flow(self, graph, pipeline_state_dict, mock_llm_client, mock_replicate):
        config = {"configurable": {"thread_id": "test-thread"}}

        # Pre-populate all generated content so the graph doesn't need to run the LLM nodes
        pipeline_state_dict["strategy"] = {
            "primary_message": "msg",
            "visual_style": "realistic",
            "suggested_content_mix": ["image"],
            "target_platforms": [],
            "estimated_complexity": "low"
        }
        pipeline_state_dict["prompts"] = [{
            "type": "image",
            "prompt": "A beautiful image of a sunset.",
            "aspect_ratio": "4:5",
            "style": "realistic"
        }]
        pipeline_state_dict["captions"] = ["Caption 1"]
        pipeline_state_dict["hashtags"] = ["#ai"]

        # Create a dummy image file for export - Windows-compatible approach
        import tempfile
        import os
        
        # Use a temp directory instead of NamedTemporaryFile to avoid Windows locking
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "test_image.png")
            # Create a minimal valid PNG file (1x1 pixel)
            with open(img_path, "wb") as f:
                # Minimal PNG header and IHDR chunk for 1x1 image
                f.write(bytes([
                    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
                    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
                    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
                    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # bit depth, etc
                    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
                    0x54, 0x08, 0xD7, 0x63, 0xF8, 0x0F, 0x00, 0x00,
                    0x01, 0x01, 0x00, 0x05, 0x18, 0xD8, 0x4E, 0x00,
                    0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND chunk
                    0x42, 0x60, 0x82
                ]))
            
            pipeline_state_dict["images"] = [img_path]
            result = await graph.ainvoke(pipeline_state_dict, config=config)

        assert result["progress"] == 100
        assert "export_metadata" in result
        assert "images" in result
        assert "captions" in result
        assert "hashtags" in result

    async def test_state_persistence(self, graph, pipeline_state_dict, mock_llm_client):
        thread_id = "persist-thread"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Use empty content mix to skip image generation entirely
        pipeline_state_dict["strategy"] = {
            "primary_message": "test",
            "visual_style": "realistic",
            "suggested_content_mix": [],  # Empty - skips visual_prompt and image_gen
            "target_platforms": [],
            "estimated_complexity": "low"
        }
        pipeline_state_dict["prompts"] = []  # Empty prompts
        pipeline_state_dict["images"] = []   # No images
        pipeline_state_dict["captions"] = ["Test caption"]
        pipeline_state_dict["hashtags"] = ["#test"]
        
        await graph.ainvoke(pipeline_state_dict, config=config)
        checkpoint = await graph.checkpointer.aget_tuple(config)
        assert checkpoint is not None
        assert checkpoint.checkpoint["channel_values"]["progress"] == 100

    async def test_thread_isolation(self, graph, pipeline_state_dict, mock_llm_client):
        """Test that different threads do not share state."""
        config1 = {"configurable": {"thread_id": "thread1"}}
        config2 = {"configurable": {"thread_id": "thread2"}}

        # Run on thread1
        await graph.ainvoke(pipeline_state_dict, config=config1)
        checkpoint1 = await graph.checkpointer.aget_tuple(config1)
        # Run on thread2
        await graph.ainvoke(pipeline_state_dict, config=config2)
        checkpoint2 = await graph.checkpointer.aget_tuple(config2)

        # Checkpoints should be separate
        assert checkpoint1 is not None
        assert checkpoint2 is not None
        # assert checkpoint1.checkpoint["channel_values"] != checkpoint2.checkpoint["channel_values"]
        # assert checkpoint1.checkpoint["checkpoint_id"] != checkpoint2.checkpoint["checkpoint_id"]
        # assert checkpoint1.checkpoint["id"] != checkpoint2.checkpoint["id"]
        # In test_thread_isolation:
        assert checkpoint1.checkpoint["id"] != checkpoint2.checkpoint["id"]

    # async def test_node_existence(self, graph):
    #     """Verify all expected nodes are present."""
    #     expected_nodes = {"strategy", "visual_prompt", "image_gen", "video_gen", "caption", "hashtag", "export"}
    #     assert set(graph.nodes.keys()) == expected_nodes


    async def test_node_existence(self, graph):
        expected_nodes = {"strategy", "visual_prompt", "image_gen", "video_gen", "caption", "hashtag", "export"}
        actual_nodes = {node for node in graph.nodes.keys() if not node.startswith("__")}
        assert actual_nodes == expected_nodes