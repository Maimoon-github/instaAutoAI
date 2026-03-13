import json

from django.contrib import admin
from django.utils.html import format_html

from .models import GenerationJob


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    """
    Admin configuration for GenerationJob.

    request_data and result_data are displayed as pretty-printed JSON in
    read-only text areas.  All status-transition fields are read-only to
    prevent accidental manual edits that bypass the pipeline state machine.
    """

    # ── List view ─────────────────────────────────────────────────────────────
    list_display   = ["job_id", "status_badge", "created_at", "completed_at", "vram_peak_mb"]
    list_filter    = ["status", "created_at"]
    search_fields  = ["job_id", "celery_task_id", "error_message"]
    date_hierarchy = "created_at"
    ordering       = ["-created_at"]

    # ── Detail view ───────────────────────────────────────────────────────────
    readonly_fields = [
        "job_id",
        "status",
        "celery_task_id",
        "checkpoint_path",
        "vram_peak_mb",
        "error_message",
        "created_at",
        "completed_at",
        "pretty_request_data",
        "pretty_result_data",
    ]

    fieldsets = [
        ("Identity", {
            "fields": ["job_id", "status", "celery_task_id", "checkpoint_path"],
        }),
        ("Payload", {
            "fields": ["pretty_request_data", "pretty_result_data"],
            "classes": ["collapse"],
        }),
        ("Assets", {
            "fields": ["image_file", "video_file"],
        }),
        ("Telemetry", {
            "fields": ["vram_peak_mb", "error_message"],
        }),
        ("Timestamps", {
            "fields": ["created_at", "completed_at"],
        }),
    ]

    # ── Custom display columns ─────────────────────────────────────────────────

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj: GenerationJob) -> str:
        colours = {
            "queued":  "#888",
            "running": "#d97706",
            "done":    "#16a34a",
            "failed":  "#dc2626",
        }
        colour = colours.get(obj.status, "#888")
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>',
            colour,
            obj.get_status_display(),
        )

    @admin.display(description="Request data")
    def pretty_request_data(self, obj: GenerationJob) -> str:
        if not obj.request_data:
            return "—"
        return format_html(
            "<pre style='font-size:12px;max-height:300px;overflow:auto'>{}</pre>",
            json.dumps(obj.request_data, indent=2, default=str),
        )

    @admin.display(description="Result data")
    def pretty_result_data(self, obj: GenerationJob) -> str:
        if not obj.result_data:
            return "—"
        return format_html(
            "<pre style='font-size:12px;max-height:300px;overflow:auto'>{}</pre>",
            json.dumps(obj.result_data, indent=2, default=str),
        )