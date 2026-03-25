from django.urls import re_path

from .consumers import JobProgressConsumer

# Imported in config/asgi.py as websocket_urlpatterns.
# re_path is required — Django's path() converters do not work with
# Channels URL routing, and the UUID regex must be explicit.
websocket_urlpatterns = [
    re_path(
        r"^ws/jobs/(?P<job_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$",
        JobProgressConsumer.as_asgi(),
        name="ws-job-progress",
    ),
]