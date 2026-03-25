"""
Unit tests for individual pipeline nodes.
Nodes are tested in isolation, with external dependencies mocked.
"""

import pytest
from unittest.mock import AsyncMock, patch

from apps.pipeline.nodes.strategy import strategy_node
from apps.pipeline.nodes.visual_prompt import visual_prompt_node
from apps.pipeline.nodes.image_gen import image_gen_node
from apps.pipeline.nodes.video_gen import video_gen_node
from apps.pipeline.nodes.caption import caption_node
from apps.pipeline.nodes.hashtag import hashtag_node
from apps.pipeline.nodes.export import export_node


pytestmark = pytest.mark.asyncio


class TestStrategyNode:
    async def test_strategy_node_success(self, mock_llm_client, pipeline_state_dict):
        """Should return strategy dict and progress update."""
        result = await strategy_node(pipeline_state_dict)
        assert "strategy" in result
        assert result["progress"] == 10
        assert result["current_node"] == "strategy"

    async def test_strategy_node_handles_error(self, mock_llm_client, pipeline_state_dict):
        """Should return error on LLM failure."""
        mock_llm_client.generate_structured.side_effect = Exception("API error")
        result = await strategy_node(pipeline_state_dict)
        assert "error" in result
        assert result["progress"] == -1


class TestVisualPromptNode:
    async def test_generates_prompts(self, mock_llm_client, pipeline_state_dict):
        """Should generate a list of prompts."""
        # Add a strategy to state
        pipeline_state_dict["strategy"] = {
            "primary_message": "Test message",
            "visual_style": "realistic",
            "suggested_content_mix": ["image", "video"]
        }
        mock_llm_client.generate.return_value = "Generated prompt"
        result = await visual_prompt_node(pipeline_state_dict)
        assert "prompts" in result
        assert len(result["prompts"]) == 2
        assert result["progress"] == 20

    async def test_handles_empty_mix(self, mock_llm_client, pipeline_state_dict):
        """Should return empty prompts list when no content mix."""
        pipeline_state_dict["strategy"] = {"suggested_content_mix": []}
        result = await visual_prompt_node(pipeline_state_dict)
        assert result["prompts"] == []


class TestImageGenNode:
    async def test_generates_images(self, mock_replicate, pipeline_state_dict):
        """Should generate images from prompts."""
        pipeline_state_dict["prompts"] = [{"type": "image", "prompt": "test", "aspect_ratio": "4:5"}]
        result = await image_gen_node(pipeline_state_dict)
        assert "images" in result
        assert len(result["images"]) == 1
        assert result["images"][0] == "http://example.com/image.png"

    async def test_handles_no_prompts(self, pipeline_state_dict):
        """Should return error when no prompts."""
        result = await image_gen_node(pipeline_state_dict)
        assert "error" in result

    async def test_handles_failure(self, mock_replicate, pipeline_state_dict):
        """Should return error when all generations fail."""
        pipeline_state_dict["prompts"] = [{"type": "image", "prompt": "test"}]
        mock_replicate.async_create.return_value.status = "failed"
        result = await image_gen_node(pipeline_state_dict)
        assert "error" in result


class TestVideoGenNode:
    async def test_no_video_prompts(self, pipeline_state_dict):
        """Should return empty videos list when no video prompts."""
        result = await video_gen_node(pipeline_state_dict)
        assert result["videos"] == []

    async def test_composes_video(self, pipeline_state_dict, tmp_path):
        """Should compose video from images (mocked FFmpeg)."""
        # Mock images list
        pipeline_state_dict["images"] = ["/tmp/img1.png", "/tmp/img2.png"]
        pipeline_state_dict["prompts"] = [{"type": "video"}]
        # Patch _run_ffmpeg to avoid actual execution
        with patch("apps.pipeline.nodes.video_gen._run_ffmpeg", new=AsyncMock()):
            result = await video_gen_node(pipeline_state_dict)
        assert "videos" in result
        assert len(result["videos"]) == 1
        assert result["progress"] == 60


class TestCaptionNode:
    async def test_generates_captions(self, mock_llm_client, pipeline_state_dict):
        """Should generate captions from LLM."""
        mock_llm_client.generate_structured.return_value = ["Caption 1", "Caption 2"]
        result = await caption_node(pipeline_state_dict)
        assert "captions" in result
        assert len(result["captions"]) == 2
        assert result["progress"] == 70


class TestHashtagNode:
    async def test_generates_hashtags(self, mock_llm_client, pipeline_state_dict):
        """Should generate hashtags from LLM."""
        mock_llm_client.generate_structured.return_value = ["ai", "tech"]
        result = await hashtag_node(pipeline_state_dict)
        assert "hashtags" in result
        assert result["hashtags"] == ["#ai", "#tech"]
        assert result["progress"] == 80


class TestExportNode:
    async def test_exports_assets(self, pipeline_state_dict, tmp_path, settings):
        """Should upload assets to storage and return metadata."""
        settings.MEDIA_ROOT = str(tmp_path)
        settings.MEDIA_URL = "/media/"
        pipeline_state_dict["job_id"] = "test-job"
        pipeline_state_dict["images"] = [str(tmp_path / "img.png")]
        pipeline_state_dict["videos"] = []
        pipeline_state_dict["captions"] = ["Cap"]
        pipeline_state_dict["hashtags"] = ["#test"]

        # Create a dummy image file
        with open(pipeline_state_dict["images"][0], "w") as f:
            f.write("dummy")

        result = await export_node(pipeline_state_dict)
        assert "export_metadata" in result
        assert result["progress"] == 100
        assert "image_urls" in result["export_metadata"]
        assert result["export_metadata"]["captions"] == ["Cap"]

    async def test_handles_upload_failure(self, pipeline_state_dict, tmp_path, settings, monkeypatch):
        """Should return error when upload fails."""
        settings.MEDIA_ROOT = str(tmp_path)
        settings.MEDIA_URL = "/media/"
        pipeline_state_dict["images"] = [str(tmp_path / "img.png")]
        # Mock upload to raise exception
        async def mock_upload(*a, **kw):
            raise Exception("Upload failed")
        monkeypatch.setattr("apps.pipeline.nodes.export._upload_file", mock_upload)
        result = await export_node(pipeline_state_dict)
        assert "error" in result