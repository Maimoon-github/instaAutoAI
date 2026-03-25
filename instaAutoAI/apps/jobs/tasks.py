"""
Celery task bridge for the InstaAutoAI pipeline.

There is exactly one task: ``execute_pipeline``.  It is enqueued by the
``post_save`` signal in ``signals.py`` (via ``transaction.on_commit``) when
a new ``GenerationJob`` is created with ``status="queued"``.

Celery workers are synchronous processes.  The LangGraph pipeline is fully
async.  ``asyncio.run()`` bridges the two worlds — it creates a fresh event
loop for each task execution, runs the pipeline to completion, then tears
the loop down.  This is the correct pattern; do NOT use
``asyncio.get_event_loop().run_until_complete()`` which is deprecated in
Python 3.10+ and raises ``DeprecationWarning`` in 3.12.

Worker settings (enforced in config/celery.py + supervisord.conf):
    --concurrency=1             one job at a time
    worker_max_tasks_per_child=1 restart after each task → flushes VRAM refs
    task_acks_late=True         ack only after task completes → no lost jobs
    task_reject_on_worker_lost=True  re-queue on SIGKILL → no silent failures
"""
import asyncio
import logging

from celery import shared_task

from .models import GenerationJob

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="jobs.execute_pipeline",
    max_retries=0,                   # no auto-retry; user resubmits failed jobs
    task_track_started=True,         # Celery backend shows STARTED state
    task_acks_late=True,             # ack only after task body completes
    task_reject_on_worker_lost=True, # re-queue if worker is killed mid-task
    serializer="json",               # never use pickle (security)
)
def execute_pipeline(self, job_id: str, request_data: dict) -> None:
    """
    Run the LangGraph pipeline for a single generation job.

    Parameters
    ----------
    job_id       : UUID string — matches ``GenerationJob.job_id`` and the
                   LangGraph ``thread_id`` used for checkpoint correlation.
    request_data : Validated ``GenerationRequest`` dict from the API.

    The task:
    1. Marks the job ``running`` with this Celery task ID.
    2. Delegates to the async ``run_pipeline`` coroutine via ``asyncio.run``.
    3. Any unhandled exception marks the job ``failed`` — the pipeline's own
       error_handler_node handles node-level failures internally.

    Note: Django model objects must NOT be passed as task arguments.  Only
    primitive types (str, dict) are accepted here, per Celery best practices.
    """
    logger.info(
        "Task %s: starting pipeline for job %s",
        self.request.id,
        job_id,
    )

    # Mark job as running and record the Celery task ID for introspection.
    try:
        job = GenerationJob.objects.get(pk=job_id)
    except GenerationJob.DoesNotExist:
        logger.error(
            "Task %s: GenerationJob %s not found — was it deleted before "
            "the worker started?",
            self.request.id,
            job_id,
        )
        return

    job.mark_running(celery_task_id=self.request.id)

    try:
        # asyncio.run() creates a fresh event loop, runs the coroutine,
        # and closes the loop — correct pattern for bridging sync Celery
        # workers to async LangGraph pipelines.
        asyncio.run(_run_pipeline_async(job_id, request_data))

    except Exception as exc:  # noqa: BLE001
        # Catch-all safety net.  run_pipeline() itself marks the job failed
        # on known pipeline errors; this catches truly unexpected exceptions
        # (e.g. asyncio loop creation failure, import errors).
        logger.exception(
            "Task %s: unhandled exception for job %s: %s",
            self.request.id,
            job_id,
            exc,
        )
        try:
            job.refresh_from_db()
            if job.status not in (
                GenerationJob.Status.DONE,
                GenerationJob.Status.FAILED,
            ):
                job.mark_failed(f"Unhandled worker error: {exc}")
        except Exception:  # noqa: BLE001
            logger.exception(
                "Task %s: could not mark job %s failed after exception",
                self.request.id,
                job_id,
            )


async def _run_pipeline_async(job_id: str, request_data: dict) -> None:
    """
    Thin async shim that imports and calls the pipeline runner.

    The import is deferred to avoid loading the entire pipeline package
    (torch, diffusers, langgraph, crewai) at worker startup — they only
    load when a task actually runs.
    """
    from apps.pipeline.runner import run_pipeline  # deferred import

    await run_pipeline(job_id, request_data)