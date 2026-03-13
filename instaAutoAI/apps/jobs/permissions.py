from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import GenerationJob


class IsLocalOrAuthenticated(BasePermission):
    """
    Grants access to requests originating from localhost without requiring
    authentication (single-user local app pattern).  Remote clients must
    be authenticated.

    WARNING: REMOTE_ADDR can be spoofed behind an incorrectly configured
    proxy.  Safe only when running on 127.0.0.1 without a public-facing
    proxy.  Configure SECURE_PROXY_SSL_HEADER for public deployments.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        remote_addr = request.META.get("REMOTE_ADDR", "")
        if remote_addr in ("127.0.0.1", "::1", "localhost"):
            return True
        return bool(request.user and request.user.is_authenticated)


class IsJobOwner(BasePermission):
    """
    Object-level permission that grants access only when the requesting
    user owns the job.

    In this single-user local app all authenticated (or local) requests
    are treated as the owner.  Override `has_object_permission` to add
    per-user ownership checks when multi-tenancy is introduced.
    """

    message = "You do not have permission to access this job."

    def has_object_permission(
        self, request: Request, view: APIView, obj: GenerationJob
    ) -> bool:
        # Single-user app: any locally-trusted or authenticated request
        # is the implicit owner.  Extend this for multi-user scenarios.
        if not (request.user and request.user.is_authenticated):
            remote_addr = request.META.get("REMOTE_ADDR", "")
            return remote_addr in ("127.0.0.1", "::1", "localhost")
        return True


class HasNoActiveJob(BasePermission):
    """
    Denies job creation when a job is already queued or running.

    This is an API-layer guard for fast rejection.  The definitive
    concurrency control is the Redis VRAM lock in VRAMManager — this
    permission exists so the user receives a clean 503 before the
    Celery task is even enqueued.

    Note: There is an inherent TOCTOU race between this check and the
    actual job creation.  The Redis lock is the safety net; this is the
    user-facing early exit.
    """

    message = (
        "A generation job is already queued or running. "
        "Only one job may execute at a time."
    )

    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method != "POST":
            return True
        active = GenerationJob.objects.filter(
            status__in=[
                GenerationJob.Status.QUEUED,
                GenerationJob.Status.RUNNING,
            ]
        ).exists()
        return not active