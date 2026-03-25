"""
Async context manager for PyTorch VRAM management.

Provides allocation tracking, OOM prevention, and automatic cache clearing.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

import torch
from django.conf import settings

logger = logging.getLogger(__name__)


class VRAMManager:
    """
    Manage GPU memory allocations with pre‑flight checks and automatic cleanup.

    Usage:
        async with VRAMManager(required_mb=1024) as manager:
            # load models, run inference
    """

    def __init__(self, required_mb: Optional[int] = None, device: int = 0):
        self.required_mb = required_mb
        self.device = device
        self._initial_allocated = 0

    @asynccontextmanager
    async def __call__(self):
        if not torch.cuda.is_available():
            logger.warning("CUDA not available; VRAM manager disabled.")
            yield
            return

        # Ensure we're on the correct device
        torch.cuda.set_device(self.device)

        # Pre-flight check: ensure enough free memory
        if self.required_mb is not None:
            free_mb = self._get_free_memory_mb()
            if free_mb < self.required_mb:
                # Try to free cached memory
                torch.cuda.empty_cache()
                free_mb = self._get_free_memory_mb()
                if free_mb < self.required_mb:
                    raise VRAMException(
                        f"Insufficient VRAM: need {self.required_mb} MB, only {free_mb} MB available"
                    )

        self._initial_allocated = torch.cuda.memory_allocated(self.device) / 1024**2
        try:
            yield
        finally:
            # Clean up after operations
            torch.cuda.empty_cache()
            final_allocated = torch.cuda.memory_allocated(self.device) / 1024**2
            logger.debug(
                "VRAM usage: initial %.1f MB → final %.1f MB (Δ %.1f MB)",
                self._initial_allocated,
                final_allocated,
                final_allocated - self._initial_allocated,
            )

    def _get_free_memory_mb(self) -> float:
        """Return free VRAM in MB."""
        total = torch.cuda.get_device_properties(self.device).total_memory / 1024**2
        allocated = torch.cuda.memory_allocated(self.device) / 1024**2
        reserved = torch.cuda.memory_reserved(self.device) / 1024**2
        # Free memory is total minus what's allocated (actual used) minus cached (reserved - allocated)
        free = total - reserved
        return free

    @staticmethod
    async def preflight_check(required_mb: int, device: int = 0) -> bool:
        """Async check if enough VRAM is available."""
        if not torch.cuda.is_available():
            return False
        # Run in a thread to avoid blocking asyncio
        return await asyncio.to_thread(
            lambda: torch.cuda.get_device_properties(device).total_memory / 1024**2
            - torch.cuda.memory_reserved(device) / 1024**2
            >= required_mb
        )