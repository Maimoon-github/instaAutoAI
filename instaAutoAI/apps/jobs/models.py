from uuid import uuid4

from django.db import models
from django.utils import timezone


class GenerationJob(models.Model):
    """
    Single source of truth for every AI content generation job.

    Lifecycle:  queued → running → done | failed

    Fields
    ------
    job_id          UUID primary key — also used as LangGraph thread_id
                    for checkpoint correlation.
    status          TextChoices enum with DB index for fast queue queries.
    request_data    Full GenerationRequest dict stored as JSON.
    result_data     GenerationResult dict (no binary data — use file fields).
    image_file      Z-Image-Turbo PNG output.
    video_file      LTX-2.3 MP4 output.
    vram_peak_mb    Peak VRAM allocation in MB — telemetry, set by export_node.
    error_message   Populated on failure; cleared on re-queue.
    celery_task_id  Celery AsyncResult ID for introspection.
    checkpoint_path Correlation key for AsyncPostgresSaver checkpoint row.
    """

    class Status(models.TextChoices):
        QUEUED  = "queued",  "Queued"
        RUNNING = "running", "Running"
        DONE    = "done",    "Done"
        FAILED  = "failed",  "Failed"

    # ── Identity ──────────────────────────────────────────────────────────────
    job_id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
    )

    # ── State ─────────────────────────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
        db_index=True,
    )
    error_message = models.TextField(null=True, blank=True)

    # ── Payload ───────────────────────────────────────────────────────────────
    request_data = models.JSONField()
    result_data  = models.JSONField(null=True, blank=True)

    # ── Assets (FileField — never base64 in JSONField) ────────────────────────
    image_file = models.FileField(
        upload_to="jobs/%Y/%m/",
        null=True,
        blank=True,
    )
    video_file = models.FileField(
        upload_to="jobs/%Y/%m/",
        null=True,
        blank=True,
    )

    # ── Telemetry ─────────────────────────────────────────────────────────────
    vram_peak_mb   = models.FloatField(null=True, blank=True)
    celery_task_id = models.CharField(max_length=255, null=True, blank=True)

    # ── LangGraph checkpoint correlation ──────────────────────────────────────
    # Stores the thread_id used with AsyncPostgresSaver so checkpoint rows
    # can be located and cleaned up without scanning all checkpoints.
    checkpoint_path = models.CharField(max_length=255, null=True, blank=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at   = models.DateTimeField(auto_now_add=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "jobs_generationjob"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    # ── Convenience mutators ──────────────────────────────────────────────────

    def mark_running(self, celery_task_id: str | None = None) -> None:
        """Transition to running; record Celery task ID."""
        self.status = self.Status.RUNNING
        if celery_task_id:
            self.celery_task_id = celery_task_id
        self.save(update_fields=["status", "celery_task_id"])

    def mark_done(
        self,
        result_data: dict,
        image_path: str | None = None,
        video_path: str | None = None,
        vram_peak_mb: float | None = None,
    ) -> None:
        """Transition to done; write result payload and asset paths."""
        self.status       = self.Status.DONE
        self.result_data  = result_data
        self.completed_at = timezone.now()
        if image_path:
            self.image_file.name = image_path
        if video_path:
            self.video_file.name = video_path
        if vram_peak_mb is not None:
            self.vram_peak_mb = vram_peak_mb
        self.save(update_fields=[
            "status", "result_data", "completed_at",
            "image_file", "video_file", "vram_peak_mb",
        ])

    def mark_failed(self, error: str) -> None:
        """Transition to failed; record error message."""
        self.status        = self.Status.FAILED
        self.error_message = error
        self.completed_at  = timezone.now()
        self.save(update_fields=["status", "error_message", "completed_at"])

    def reset_for_retry(self) -> None:
        """Reset a failed job back to queued for manual retry."""
        self.status        = self.Status.QUEUED
        self.error_message = None
        self.completed_at  = None
        self.save(update_fields=["status", "error_message", "completed_at"])

    def __str__(self) -> str:
        return f"{self.job_id} ({self.status})"