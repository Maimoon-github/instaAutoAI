# """
# Base utilities for pipeline nodes: rate limiting, retries, error handling.
# """

# import asyncio
# import functools
# import logging
# from typing import Any, Callable, Dict, Optional, TypeVar, Union

# from tenacity import (
#     retry,
#     stop_after_attempt,
#     wait_exponential,
#     retry_if_exception_type,
#     before_sleep_log,
# )

# from ..exceptions import LLMRateLimitError
# from ..state import PipelineState

# logger = logging.getLogger(__name__)

# T = TypeVar("T")


# class RateLimiter:
#     """Async rate limiter using semaphore and optional delay between calls."""

#     def __init__(self, max_concurrent: int, delay_seconds: float = 0.0):
#         self._semaphore = asyncio.Semaphore(max_concurrent)
#         self._delay = delay_seconds

#     async def __aenter__(self):
#         await self._semaphore.acquire()
#         return self

#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         self._semaphore.release()
#         if self._delay > 0:
#             await asyncio.sleep(self._delay)

#     async def run(self, coro):
#         """Acquire semaphore, run coroutine, release after."""
#         async with self:
#             return await coro


# def retry_async(
#     retry_exceptions: tuple = (LLMRateLimitError,),
#     attempts: int = 3,
#     min_wait: float = 1.0,
#     max_wait: float = 60.0,
# ) -> Callable:
#     """Decorator for retrying async functions with exponential backoff."""
#     return retry(
#         retry=retry_if_exception_type(retry_exceptions),
#         stop=stop_after_attempt(attempts),
#         wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
#         before_sleep=before_sleep_log(logger, logging.WARNING),
#         reraise=True,
#     )


# def node(
#     func: Callable[..., Any],
#     rate_limiter: Optional[RateLimiter] = None,
#     retry_config: Optional[Dict] = None,
# ) -> Callable[[PipelineState], Any]:
#     """
#     Wrap a node function to inject rate limiting and retry logic.

#     Usage:
#         @node(rate_limiter=ai_limiter, retry_config={"attempts": 3})
#         async def my_node(state: PipelineState) -> dict:
#             ...
#     """
#     # Apply retry decorator if needed
#     if retry_config:
#         func = retry_async(**retry_config)(func)

#     @functools.wraps(func)
#     async def wrapper(state: PipelineState, **kwargs) -> dict:
#         try:
#             if rate_limiter:
#                 return await rate_limiter.run(func(state, **kwargs))
#             else:
#                 return await func(state, **kwargs)
#         except Exception as e:
#             logger.exception("Node %s failed: %s", func.__name__, e)
#             # Return error update to be merged into state
#             return {"error": str(e), "progress": -1}
#     return wrapper

































"""
Base utilities for pipeline nodes: rate limiting, retries, error handling.
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from ..exceptions import LLMRateLimitError
from ..state import PipelineState

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimiter:
    """Async rate limiter using semaphore and optional delay between calls."""

    def __init__(self, max_concurrent: int, delay_seconds: float = 0.0):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._delay = delay_seconds

    async def __aenter__(self):
        await self._semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._semaphore.release()
        if self._delay > 0:
            await asyncio.sleep(self._delay)

    async def run(self, coro):
        """Acquire semaphore, run coroutine, release after."""
        async with self:
            return await coro


def retry_async(
    retry_exceptions: tuple = (LLMRateLimitError,),
    attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 60.0,
) -> Callable:
    """Decorator for retrying async functions with exponential backoff."""
    return retry(
        retry=retry_if_exception_type(retry_exceptions),
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


def node(
    func: Optional[Callable[..., Any]] = None,
    *,
    rate_limiter: Optional[RateLimiter] = None,
    retry_config: Optional[Dict] = None,
) -> Callable:
    """
    Wrap a node function to inject rate limiting and retry logic.

    Usage:
        @node(rate_limiter=ai_limiter, retry_config={"attempts": 3})
        async def my_node(state: PipelineState) -> dict:
            ...

        Or without parameters:
        @node
        async def my_node(state: PipelineState) -> dict:
            ...
    """
    # Inner decorator that actually wraps the function
    def decorator(f: Callable[..., Any]) -> Callable[[PipelineState], Any]:
        # Apply retry decorator if needed
        wrapped = f
        if retry_config:
            wrapped = retry_async(**retry_config)(f)

        @functools.wraps(f)
        async def wrapper(state: PipelineState, **kwargs) -> dict:
            try:
                if rate_limiter:
                    return await rate_limiter.run(wrapped(state, **kwargs))
                else:
                    return await wrapped(state, **kwargs)
            except Exception as e:
                logger.exception("Node %s failed: %s", f.__name__, e)
                # Return error update to be merged into state
                return {"error": str(e), "progress": -1}
        return wrapper

    # If func is provided directly (used as @node without parentheses), apply immediately
    if func is not None:
        return decorator(func)
    
    # Otherwise return the decorator (used as @node(...))
    return decorator