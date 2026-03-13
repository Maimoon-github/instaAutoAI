"""
Custom middleware for security, logging, and monitoring.
"""

import time
import logging
import uuid
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RequestIDMiddleware(MiddlewareMixin):
    """
    Add a unique request ID to the request object and to the response headers.
    Useful for tracing requests in logs.
    """
    def process_request(self, request):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.id = request_id

    def process_response(self, request, response):
        if hasattr(request, "id"):
            response["X-Request-ID"] = request.id
        return response


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Log request duration and add X-Page-Generation-Duration header.
    """
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
            response["X-Page-Generation-Duration"] = f"{duration:.4f}s"
            logger.info(f"Request to {request.path} took {duration:.4f}s")
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security-related headers to every response.
    """
    def process_response(self, request, response):
        response["X-Frame-Options"] = "DENY"
        response["X-Content-Type-Options"] = "nosniff"
        response["Referrer-Policy"] = "same-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # Optionally add X-XSS-Protection (though modern browsers ignore it)
        response["X-XSS-Protection"] = "1; mode=block"
        return response


class CSPMiddleware(MiddlewareMixin):
    """
    Set Content‑Security‑Policy header.
    For production, integrate with django‑csp instead of this simple version.
    """
    def process_response(self, request, response):
        # This is a minimal example; use django‑csp for full control.
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "  # unsafe-inline only for development
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:;"
        )
        response["Content-Security-Policy"] = csp
        return response


class ExceptionLoggingMiddleware(MiddlewareMixin):
    """
    Catch unhandled exceptions, log them, and optionally notify admins.
    """
    def process_exception(self, request, exception):
        logger.exception(
            "Unhandled exception for request %s %s: %s",
            request.method,
            request.path,
            str(exception),
            exc_info=True,
        )
        # Optionally send email to ADMINS here
        return None  # Let Django handle the response