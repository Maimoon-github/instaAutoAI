from django.urls import path

from .views import (
    DashboardView,
    GenerateView,
    JobDetailView,
    JobListView,
    JobVRAMView,
)

# Mounted at the root in config/urls.py:
#   path("", include("apps.jobs.urls"))          → dashboard at /
#   path("api/v1/", include("apps.jobs.urls"))   → REST API
#
# Full resolved paths:
#   GET  /                                  → dashboard.html
#   POST /api/v1/generate/                  → create job
#   GET  /api/v1/jobs/                      → job history list
#   GET  /api/v1/jobs/<uuid>/               → job detail
#   GET  /api/v1/jobs/<uuid>/vram/          → live VRAM snapshot

urlpatterns = [
    # Dashboard — serves the single-file Alpine.js UI at the site root.
    path("", DashboardView.as_view(), name="dashboard"),

    # Job creation — returns {job_id, status: "queued"} immediately.
    path("api/v1/generate/", GenerateView.as_view(), name="job-generate"),

    # Job history list — filterable, paginated.
    path("api/v1/jobs/", JobListView.as_view(), name="job-list"),

    # Job detail — full serialized job state with absolute asset URLs.
    # <uuid:job_id> validates UUID format and returns 404 on malformed input.
    path("api/v1/jobs/<uuid:job_id>/", JobDetailView.as_view(), name="job-detail"),

    # Live VRAM snapshot — polled every 2 s by the frontend sparkline.
    path("api/v1/jobs/<uuid:job_id>/vram/", JobVRAMView.as_view(), name="job-vram"),
]