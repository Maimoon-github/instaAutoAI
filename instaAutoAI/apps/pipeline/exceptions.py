"""
Custom exception hierarchy for pipeline operations.
"""

class PipelineException(Exception):
    """Base exception for pipeline errors."""
    pass


class VRAMException(PipelineException):
    """Raised when VRAM allocation fails (e.g., OOM)."""
    pass


class StateCorruptionError(PipelineException):
    """Raised when checkpoint data is corrupted or missing."""
    pass


class LLMRateLimitError(PipelineException):
    """Raised when LLM API rate limit is exceeded (retryable)."""
    pass


class AgentTimeoutError(PipelineException):
    """Raised when CrewAI agent task times out."""
    pass