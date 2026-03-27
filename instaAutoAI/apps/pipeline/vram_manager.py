"""
Async context manager for PyTorch VRAM management.
"""

import asyncio
import logging
from typing import Optional

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

from .exceptions import VRAMException

logger = logging.getLogger(__name__)


class VRAMManager:
    """
    Manage GPU memory allocations with pre‑flight checks and automatic cleanup.
    If torch is not available, the manager becomes a no‑op.
    """

    def __init__(self, required_mb: Optional[int] = None, device: int = 0):
        self.required_mb = required_mb
        self.device = device
        self._initial_allocated = 0

    async def __aenter__(self):
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            logger.warning("CUDA not available or torch missing; VRAM manager disabled.")
            return self

        torch.cuda.set_device(self.device)

        if self.required_mb is not None:
            free_mb = self._get_free_memory_mb()
            if free_mb < self.required_mb:
                torch.cuda.empty_cache()
                free_mb = self._get_free_memory_mb()
                if free_mb < self.required_mb:
                    raise VRAMException(
                        f"Insufficient VRAM: need {self.required_mb} MB, only {free_mb} MB available"
                    )

        self._initial_allocated = torch.cuda.memory_allocated(self.device) / 1024**2
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return

        torch.cuda.empty_cache()
        final_allocated = torch.cuda.memory_allocated(self.device) / 1024**2
        logger.info(
            "VRAM usage: initial %.1f MB → final %.1f MB (Δ %.1f MB)",
            self._initial_allocated,
            final_allocated,
            final_allocated - self._initial_allocated,
        )

    def _get_free_memory_mb(self) -> float:
        """Return free VRAM in MB."""
        total = torch.cuda.get_device_properties(self.device).total_memory / 1024**2
        reserved = torch.cuda.memory_reserved(self.device) / 1024**2
        free = total - reserved
        return free

    @staticmethod
    async def preflight_check(required_mb: int, device: int = 0) -> bool:
        """Async check if enough VRAM is available."""
        if not TORCH_AVAILABLE or not torch.cuda.is_available():
            return False
        # Run in a thread to avoid blocking asyncio
        return await asyncio.to_thread(
            lambda: torch.cuda.get_device_properties(device).total_memory / 1024**2
            - torch.cuda.memory_reserved(device) / 1024**2
            >= required_mb
        )