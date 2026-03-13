"""
Reusable mixins for class-based views.
"""

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.vary import vary_on_headers
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.throttling import UserRateThrottle
from core.utils import get_client_ip
from core.constants import VRAM_LOCK_KEY


class AgentAPIAuthMixin(BasePermission):
    """
    Permission class that checks for a valid API key in the request headers.
    Intended for internal agent-to-agent communication.
    """
    def has_permission(self, request, view):
        api_key = request.headers.get("X-Agent-API-Key")
        # Compare with a secure key stored in settings
        from django.conf import settings
        if api_key and api_key == settings.AGENT_API_KEY:
            return True
        return False


class JobOwnerRequiredMixin(BasePermission):
    """
    Permission class that ensures the user owns the job object.
    Assumes the view has a `get_object()` method that returns a job with a `user` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Allow if the user is authenticated and is the owner
        return request.user.is_authenticated and obj.user == request.user


class VRAMStatusMixin:
    """
    Mixin that adds VRAM usage statistics to the view context.
    For API views, it can be used to include VRAM info in the response.
    """
    def get_vram_status(self):
        # This would normally query the VRAM manager
        # For now, return a placeholder
        return {
            "total": "8 GB",
            "used": cache.get(VRAM_LOCK_KEY, 0),
            "available": "8 GB - used",
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["vram_status"] = self.get_vram_status()
        return context

    def finalize_response(self, request, response, *args, **kwargs):
        if hasattr(response, "data") and isinstance(response.data, dict):
            response.data["vram_status"] = self.get_vram_status()
        return super().finalize_response(request, response, *args, **kwargs)


class CacheControlMixin:
    """
    Mixin that applies cache control headers to the response.
    Usage: class MyView(CacheControlMixin, APIView): cache_max_age = 60
    """
    cache_max_age = 0
    cache_private = False
    cache_vary_headers = []

    @method_decorator(cache_control(max_age=cache_max_age, private=cache_private))
    @method_decorator(vary_on_headers(*cache_vary_headers))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class ThrottleMixin:
    """
    Mixin to apply rate limiting per user or IP.
    Uses Django REST Framework's throttling classes.
    """
    throttle_classes = [UserRateThrottle]

    def get_throttles(self):
        throttles = super().get_throttles()
        # Optionally add an IP-based throttle
        from rest_framework.throttling import AnonRateThrottle
        throttles.append(AnonRateThrottle())
        return throttles