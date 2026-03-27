from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    # Jobs URLs mounted at root — jobs/urls.py hardcodes its own api/v1/ prefixes,
    # so dashboard resolves at / and REST endpoints at /api/v1/generate/, /api/v1/jobs/, etc.
    # Do NOT also include under path("api/v1/", ...) — that would double-prefix
    # every route to /api/v1/api/v1/generate/ etc. and cause 503s on all job endpoints.
    path("", include(("instaAutoAI.apps.jobs.urls", "jobs"), namespace="jobs")),
    path("api/v1/", include("instaAutoAI.apps.pipeline.urls")),
    path("api/v1/", include("instaAutoAI.apps.users.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)