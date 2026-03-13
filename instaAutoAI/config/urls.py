from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("instaAutoAI.apps.jobs.urls")),
    path("api/v1/", include("instaAutoAI.apps.pipeline.urls")),
    path("api/v1/", include("instaAutoAI.apps.users.urls")),
    path("", include("instaAutoAI.apps.dashboard.urls")),  # if dashboard exists
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)