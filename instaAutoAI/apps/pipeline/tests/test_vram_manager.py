"""
Unit tests for VRAMManager with mocked CUDA.
"""

import pytest
from unittest.mock import AsyncMock, patch
import asyncio

from apps.pipeline.vram_manager import VRAMManager
from apps.pipeline.exceptions import VRAMException


pytestmark = pytest.mark.asyncio


class TestVRAMManager:
    async def test_context_manager_no_gpu(self, monkeypatch):
        """Should skip VRAM management when CUDA is not available."""
        monkeypatch.setattr("torch.cuda.is_available", lambda: False)
        manager = VRAMManager(required_mb=100)
        async with manager():
            pass  # Should not raise

    async def test_preflight_check_success(self, mock_torch_cuda):
        """Preflight check should return True when enough memory is free."""
        result = await VRAMManager.preflight_check(required_mb=1024, device=0)
        assert result is True

    async def test_preflight_check_failure(self, mock_torch_cuda):
        """Preflight check should return False when insufficient memory."""
        # Simulate low free memory
        mock_torch_cuda.memory_reserved.return_value = 7.9 * 1024**3  # almost full
        result = await VRAMManager.preflight_check(required_mb=1024, device=0)
        assert result is False

    async def test_context_manager_oom_prevention(self, mock_torch_cuda):
        """Should raise VRAMException when insufficient VRAM."""
        # Make free memory less than required
        mock_torch_cuda.memory_reserved.return_value = 7.9 * 1024**3
        manager = VRAMManager(required_mb=1024)
        with pytest.raises(VRAMException, match="Insufficient VRAM"):
            async with manager():
                pass

    async def test_context_manager_clears_cache(self, mock_torch_cuda):
        """Should call torch.cuda.empty_cache on exit."""
        manager = VRAMManager()
        async with manager():
            pass
        mock_torch_cuda.empty_cache.assert_called_once()

    async def test_context_manager_logs_usage(self, mock_torch_cuda, caplog):
        """Should log memory usage on exit."""
        manager = VRAMManager()
        async with manager():
            pass
        assert "VRAM usage: initial" in caplog.text