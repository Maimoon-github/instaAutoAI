import logging

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import GenerationJob

logger = logging.getLogger(__name__)


# ── Pre-save: capture status transitions for audit logging ────────────────────

@receiver(pre_save, sender=GenerationJob)
def log_status_transition(
    sender: type[GenerationJob],
    instance: GenerationJob,
    **kwargs,
) -> None:
    """
    Log every status transition for audit trails and debugging.

    Reads the persisted status from the DB (if the row exists) and
    compares it to the about-to-be-saved value.  Runs synchronously
    inside the save() call — do not perform heavy I/O here.
    """
    if not instance.pk:
        # New record — no prior state to compare.
        return

    try:
        previous = GenerationJob.objects.only("status").get(pk=instance.pk)
    except GenerationJob.DoesNotExist:
        return

    if previous.status != instance.status:
        logger.info(
            "Job %s status transition: %s → %s",
            instance.job_id,
            previous.status,
            instance.status,
        )


# ── Post-save: enqueue Celery task when a job is first created ────────────────

@receiver(post_save, sender=GenerationJob)
def enqueue_pipeline_task(
    sender: type[GenerationJob],
    instance: GenerationJob,
    created: bool,
    **kwargs,
) -> None:
    """
    Enqueue the Celery pipeline task when a new queued job is created.

    Uses transaction.on_commit so the task is enqueued only AFTER the
    database transaction commits and the row is visible to the Celery
    worker process.  Without this guard, the worker can start before
    the row exists and raise GenerationJob.DoesNotExist.

    Note: tasks.py is imported inside the function to break the circular
    import chain (models → tasks → models).
    """
    if not (created and instance.status == GenerationJob.Status.QUEUED):
        return

    def _enqueue() -> None:
        from .tasks import execute_pipeline  # local import breaks circular dep

        result = execute_pipeline.delay(
            str(instance.job_id),
            instance.request_data,
        )
        # Persist the Celery task ID for introspection without blocking
        # the caller — use update() to skip the full save cycle.
        GenerationJob.objects.filter(pk=instance.pk).update(
            celery_task_id=result.id
        )
        logger.info(
            "Job %s enqueued as Celery task %s",
            instance.job_id,
            result.id,
        )

    transaction.on_commit(_enqueue)


# ── Post-save: telemetry logging on terminal states ───────────────────────────

@receiver(post_save, sender=GenerationJob)
def log_terminal_state(
    sender: type[GenerationJob],
    instance: GenerationJob,
    created: bool,
    **kwargs,
) -> None:
    """Log completion metrics when a job reaches a terminal state."""
    if created:
        return

    if instance.status == GenerationJob.Status.DONE:
        duration = None
        if instance.completed_at and instance.created_at:
            duration = (instance.completed_at - instance.created_at).total_seconds()
        logger.info(
            "Job %s completed — vram_peak=%.1f MB, duration=%.0f s",
            instance.job_id,
            instance.vram_peak_mb or 0.0,
            duration or 0.0,
        )

    elif instance.status == GenerationJob.Status.FAILED:
        logger.error(
            "Job %s failed — error: %s",
            instance.job_id,
            instance.error_message or "(no message)",
        )