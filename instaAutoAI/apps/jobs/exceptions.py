from rest_framework import status
from rest_framework.exceptions import APIException


class JobNotFoundError(APIException):
    """Raised when a requested GenerationJob UUID does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Generation job not found."
    default_code = "job_not_found"


class ConcurrencyLimitError(APIException):
    """
    Raised when a new job is submitted while one is already
    queued or running.

    The Retry-After header is injected by the custom exception handler
    in core/middleware.py — not here.  This class carries the signal;
    the handler carries the header.
    """

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = (
        "A pipeline job is already running. "
        "Only one job may execute at a time due to VRAM constraints. "
        "Retry after 300 seconds."
    )
    default_code = "pipeline_busy"


class PipelineError(APIException):
    """
    Raised when the LangGraph pipeline encounters an unrecoverable error
    that should be surfaced to the API caller.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "The generation pipeline encountered an error."
    default_code = "pipeline_error"


class VRAMError(APIException):
    """
    Raised when GPU memory allocation fails or the VRAM lock cannot
    be acquired within the timeout window.
    """

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = (
        "Insufficient VRAM available to start generation. "
        "Wait for the current job to complete before retrying."
    )
    default_code = "vram_unavailable"


class CheckpointError(APIException):
    """
    Raised when the LangGraph AsyncPostgresSaver cannot read or write
    a checkpoint, preventing job resumption.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = (
        "Pipeline checkpoint operation failed. "
        "The job cannot be resumed; please resubmit."
    )
    default_code = "checkpoint_error"


class ServiceUnavailableError(APIException):
    """
    Raised when a required external service (Ollama, ComfyUI, Redis)
    is unreachable at job-submission time.
    """

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "A required service is currently unavailable."
    default_code = "service_unavailable"