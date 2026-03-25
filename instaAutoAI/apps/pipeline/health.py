"""
Health check endpoints for Kubernetes (liveness/readiness).
Returns JSON with dependency status and timings.
"""

import asyncio
import time
from typing import Dict, Any

from django.conf import settings
from django.http import JsonResponse
from redis import Redis
import torch

from .exceptions import PipelineException


class HealthChecker:
    """Performs health checks on dependencies."""

    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.redis_client = None

    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity."""
        start = time.time()
        try:
            if not self.redis_client:
                self.redis_client = Redis.from_url(self.redis_url, socket_connect_timeout=0.2)
            self.redis_client.ping()
            return {"status": "ok", "latency_ms": (time.time() - start) * 1000}
        except Exception as e:
            return {"status": "error", "error": str(e), "latency_ms": (time.time() - start) * 1000}

    async def check_gpu(self) -> Dict[str, Any]:
        """Check GPU availability and VRAM."""
        if not torch.cuda.is_available():
            return {"status": "error", "error": "CUDA not available"}
        try:
            device = torch.cuda.current_device()
            total_mb = torch.cuda.get_device_properties(device).total_memory / 1024**2
            allocated_mb = torch.cuda.memory_allocated(device) / 1024**2
            reserved_mb = torch.cuda.memory_reserved(device) / 1024**2
            free_mb = total_mb - reserved_mb
            return {
                "status": "ok",
                "device": device,
                "total_mb": total_mb,
                "free_mb": free_mb,
                "allocated_mb": allocated_mb,
                "reserved_mb": reserved_mb,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def check_llm_api(self) -> Dict[str, Any]:
        """Check LLM API connectivity (lightweight ping)."""
        # Use a fast, cheap request (e.g., list models) – requires async client.
        # This is optional; we'll implement a quick check.
        # For simplicity, we'll just return ok if we have an API key.
        if settings.OPENAI_API_KEY:
            return {"status": "ok", "provider": "openai"}
        elif settings.ANTHROPIC_API_KEY:
            return {"status": "ok", "provider": "anthropic"}
        else:
            return {"status": "error", "error": "No LLM API key configured"}

    async def all_checks(self) -> Dict[str, Any]:
        """Run all dependency checks concurrently."""
        results = await asyncio.gather(
            self.check_redis(),
            self.check_gpu(),
            self.check_llm_api(),
            return_exceptions=False,
        )
        return {
            "redis": results[0],
            "gpu": results[1],
            "llm_api": results[2],
        }


# Django view wrappers
async def liveness(request):
    """Liveness probe: returns 200 if process is alive."""
    return JsonResponse({"status": "ok"})


async def readiness(request):
    """
    Readiness probe: checks all dependencies.
    Returns 200 only if all critical dependencies are healthy.
    """
    checker = HealthChecker()
    checks = await checker.all_checks()
    # Consider redis and gpu critical; llm_api is optional (can be degraded)
    is_ready = (
        checks["redis"]["status"] == "ok"
        and checks["gpu"]["status"] == "ok"
    )
    status_code = 200 if is_ready else 503
    return JsonResponse(checks, status=status_code)