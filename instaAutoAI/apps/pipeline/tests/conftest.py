"""
Pytest configuration and fixtures for pipeline tests.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from langgraph.checkpoint.memory import MemorySaver
from asgiref.sync import sync_to_async
from django.conf import settings
from django.test import override_settings

# Force transaction=True for all async DB tests
def pytest_collection_modifyitems(config, items):
    for item in items:
        if "asyncio" in item.keywords and "django_db" in item.keywords:
            # Add transaction=True marker
            item.add_marker(pytest.mark.django_db(transaction=True))


@pytest.fixture(scope="function")
def event_loop():
    """Create a new event loop per test function."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_torch_cuda(monkeypatch):
    """Mock torch.cuda module to avoid GPU dependency in tests."""
    mock_cuda = MagicMock()
    mock_cuda.is_available.return_value = True
    mock_cuda.set_device = MagicMock()
    mock_cuda.empty_cache = MagicMock()
    mock_cuda.memory_allocated.return_value = 512 * 1024 ** 2  # 512 MB
    mock_cuda.memory_reserved.return_value = 1024 * 1024 ** 2  # 1 GB
    mock_cuda.max_memory_allocated.return_value = 768 * 1024 ** 2  # 768 MB
    device_props = MagicMock()
    device_props.total_memory = 8 * 1024 ** 3  # 8 GB
    mock_cuda.get_device_properties.return_value = device_props
    monkeypatch.setattr("torch.cuda", mock_cuda)
    return mock_cuda


@pytest.fixture
def mock_llm_client(monkeypatch):
    """Mock LLMClient to avoid actual API calls."""
    from apps.pipeline.llm_client import LLMClient
    mock_client = AsyncMock()
    mock_client.generate.return_value = "Generated response"
    mock_client.generate_structured.return_value = {"key": "value"}
    monkeypatch.setattr(LLMClient, "get_client", lambda *a, **kw: mock_client)
    return mock_client


@pytest.fixture
def mock_replicate(monkeypatch):
    """Mock replicate API to avoid actual API calls."""
    mock_predictions = AsyncMock()
    mock_prediction = AsyncMock()
    mock_prediction.status = "succeeded"
    mock_prediction.output = ["http://example.com/image.png"]
    mock_prediction.id = "mock-id"
    mock_predictions.async_create.return_value = mock_prediction
    mock_predictions.async_get.return_value = mock_prediction
    monkeypatch.setattr("replicate.predictions", mock_predictions)
    return mock_predictions


@pytest.fixture
def compiled_graph(mock_llm_client, mock_replicate):
    """Provide a compiled graph with MemorySaver for integration tests."""
    from apps.pipeline.graph import build_graph
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)
    return graph


@pytest.fixture
def pipeline_state_dict():
    """Minimal valid PipelineState dictionary for testing."""
    return {
        "job_id": "test-job-123",
        "request_data": {
            "topic": "AI productivity",
            "niche": "tech",
            "tone": "professional",
            "output_format": "image",
            "aspect_ratio": "4:5",
            "caption_length": "medium",
            "hashtag_count": 20,
            "brand_keywords": ["ai", "automation"]
        },
        "messages": [],
        "current_node": "",
        "progress": 0,
        "result": {},
        "error": None,
        "timestamp": "2025-03-25T00:00:00Z",
        "strategy": {},
        "prompts": [],
        "images": [],
        "videos": [],
        "captions": [],
        "hashtags": [],
        "export_metadata": {},
    }