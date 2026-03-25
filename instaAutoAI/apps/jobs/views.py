"""
DRF API views for the jobs app.

Endpoints
---------
GET  /                              DashboardView   → renders dashboard.html
POST /api/v1/generate/              GenerateView    → creates GenerationJob
GET  /api/v1/jobs/                  JobListView     → last 20 jobs
GET  /api/v1/jobs/<uuid:job_id>/    JobDetailView   → single job state
GET  /api/v1/jobs/<uuid:job_id>/vram/  JobVRAMView → live VRAM snapshot

Concurrency model
-----------------
``GenerateView.post`` checks ``HasNoActiveJob`` permission before creating
a job.  If a job is already queued or running, the permission returns False
and DRF raises a 403.  We override this with a custom ``handle_exception``
to emit HTTP 503 + ``Retry-After: 300`` per the DeepSpec contract.

The ``post_save`` signal in ``signals.py`` enqueues the Celery task via
``transaction.on_commit`` — views.py does NOT call ``execute_pipeline.delay``
directly.  The view creates the DB row and returns immediately.
"""
import logging
from datetime import datetime, timezone
from uuid import uuid4

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import ConcurrencyLimitError
from .filters import GenerationJobFilter
from .models import GenerationJob
from .pagination import JobPagination
from .permissions import HasNoActiveJob, IsLocalOrAuthenticated
from .serializers import (
    GenerationJobListSerializer,
    GenerationJobSerializer,
    GenerationRequestSerializer,
    VRAMSnapshotSerializer,
)

logger = logging.getLogger(__name__)

# ── VRAM helpers ──────────────────────────────────────────────────────────────

def _get_vram_snapshot() -> dict:
    """
    Return a live VRAM snapshot from torch.cuda.

    Guards with ``torch.cuda.is_available()`` — returns zeros if no GPU
    is present (e.g. CI environment, CPU-only machine).
    """
    try:
        import torch

        if not torch.cuda.is_available():
            return {
                "vram_allocated_mb": 0.0,
                "vram_reserved_mb":  0.0,
                "vram_peak_mb":      0.0,
                "vram_total_mb":     0.0,
                "timestamp":         datetime.now(tz=timezone.utc),
            }

        mb = 1024 ** 2
        return {
            "vram_allocated_mb": torch.cuda.memory_allocated()     / mb,
            "vram_reserved_mb":  torch.cuda.memory_reserved()      / mb,
            "vram_peak_mb":      torch.cuda.max_memory_allocated()  / mb,
            "vram_total_mb":     torch.cuda.get_device_properties(0).total_memory / mb,
            "timestamp":         datetime.now(tz=timezone.utc),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("VRAM snapshot failed: %s", exc)
        return {
            "vram_allocated_mb": 0.0,
            "vram_reserved_mb":  0.0,
            "vram_peak_mb":      0.0,
            "vram_total_mb":     0.0,
            "timestamp":         datetime.now(tz=timezone.utc),
        }


# ── Views ──────────────────────────────────────────────────────────────────────

class DashboardView(APIView):
    """
    GET /
    Serves the single-file Tailwind + Alpine.js dashboard.
    No authentication required — this is a local-only app.
    """

    permission_classes = []
    authentication_classes = []

    def get(self, request: Request) -> HttpResponse:
        return render(request._request, "dashboard.html")


class GenerateView(APIView):
    """
    POST /api/v1/generate/

    Validates the GenerationRequest, creates a queued GenerationJob,
    and returns immediately with ``{job_id, status: "queued"}``.

    The Celery task is enqueued by the ``post_save`` signal in signals.py
    via ``transaction.on_commit`` — this view does NOT call .delay().

    Returns
    -------
    200 OK   : ``{"job_id": str, "status": "queued"}``
    400      : Validation errors on request body.
    503      : A job is already queued or running (Retry-After: 300 header).
    """

    permission_classes = [IsLocalOrAuthenticated, HasNoActiveJob]

    def get_exception_handler(self):
        """
        Override DRF's default exception handler to inject Retry-After
        header when HasNoActiveJob permission raises 403.
        """
        from rest_framework.views import exception_handler as drf_handler

        def _handler(exc, context):
            # HasNoActiveJob returns permission denied → we want 503.
            from rest_framework.exceptions import PermissionDenied
            if isinstance(exc, PermissionDenied) and "already queued" in str(exc.detail):
                response = Response(
                    {
                        "error":  "pipeline_busy",
                        "detail": str(exc.detail),
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
                response["Retry-After"] = "300"
                return response
            return drf_handler(exc, context)

        return _handler

    def post(self, request: Request) -> Response:
        serializer = GenerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        job_id = uuid4()
        job = GenerationJob.objects.create(
            job_id=job_id,
            status=GenerationJob.Status.QUEUED,
            request_data=serializer.validated_data,
            # checkpoint_path correlates with LangGraph AsyncPostgresSaver
            checkpoint_path=str(job_id),
        )

        logger.info("Job %s created (queued)", job.job_id)

        return Response(
            {
                "job_id": str(job.job_id),
                "status": job.status,
                "ws_url": f"ws://localhost:8000/ws/jobs/{job.job_id}/",
            },
            status=status.HTTP_200_OK,
        )


class JobDetailView(APIView):
    """
    GET /api/v1/jobs/<uuid:job_id>/

    Returns the full serialized state of a single GenerationJob,
    including absolute image_url and video_url.
    """

    permission_classes = [IsLocalOrAuthenticated]

    def get(self, request: Request, job_id) -> Response:
        try:
            job = GenerationJob.objects.get(pk=job_id)
        except GenerationJob.DoesNotExist:
            from .exceptions import JobNotFoundError
            raise JobNotFoundError()

        serializer = GenerationJobSerializer(
            job,
            context={"request": request},
        )
        return Response(serializer.data)


class JobListView(APIView):
    """
    GET /api/v1/jobs/

    Returns a paginated, filterable list of the last N jobs ordered
    by descending creation time.  Uses the lightweight list serializer
    (omits large JSONField blobs) for fast response times.

    Query parameters
    ----------------
    status         : Filter by status (``queued``, ``running``, ``done``, ``failed``)
    created_after  : ISO-8601 datetime lower bound
    created_before : ISO-8601 datetime upper bound
    page           : Page number (default 1)
    page_size      : Results per page (default 20, max 100)
    """

    permission_classes = [IsLocalOrAuthenticated]
    pagination_class = JobPagination

    def get(self, request: Request) -> Response:
        queryset = GenerationJob.objects.all().order_by("-created_at")

        # Apply filters
        f = GenerationJobFilter(request.query_params, queryset=queryset)
        queryset = f.qs

        # Paginate
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        serializer = GenerationJobListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class JobVRAMView(APIView):
    """
    GET /api/v1/jobs/<uuid:job_id>/vram/

    Returns a live VRAM snapshot from ``torch.cuda``.  Polled by the
    frontend every 2 seconds to drive the VRAM sparkline chart.

    The ``job_id`` parameter is accepted for API consistency but is not
    used — VRAM state is global, not per-job.  The endpoint is scoped
    to job URLs so the frontend can use the same job_id it already has.
    """

    permission_classes = [IsLocalOrAuthenticated]

    def get(self, request: Request, job_id=None) -> Response:
        snapshot = _get_vram_snapshot()
        serializer = VRAMSnapshotSerializer(snapshot)
        return Response(serializer.data)