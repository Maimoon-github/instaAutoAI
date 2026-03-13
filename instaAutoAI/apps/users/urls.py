from django.urls import path

from .views import MeView

# Mounted at api/v1/auth/ in config/urls.py
# Full resolved URL: /api/v1/auth/me/
urlpatterns = [
    path("me/", MeView.as_view(), name="user-me"),
]