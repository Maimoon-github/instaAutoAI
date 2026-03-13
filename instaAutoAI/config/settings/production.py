"""
Production settings for instaAutoAI.
"""

from .base import *  # noqa
import logging.config

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set!")

DEBUG = False

# Must be set in production
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS environment variable is required in production!")

# Database – use PostgreSQL with connection pooling
DATABASES = {
    "default": env.db(),
}
# Enable persistent connections
DATABASES["default"]["CONN_MAX_AGE"] = 60

# HTTPS settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS – instruct browsers to always use HTTPS
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security headers
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Static files – WhiteNoise with compression and manifest
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Logging – JSON format for aggregation (e.g., Datadog, ELK)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# Optional: configure email for error reports
ADMINS = [("Admin", env("ADMIN_EMAIL", default=""))]
if ADMINS[0][1]:
    LOGGING["handlers"]["mail_admins"] = {
        "level": "ERROR",
        "class": "django.utils.log.AdminEmailHandler",
    }
    LOGGING["root"]["handlers"].append("mail_admins")

# Ensure the python-json-logger is installed (add to requirements)
try:
    import pythonjsonlogger  # noqa
except ImportError:
    raise ImportError(
        "python-json-logger is required for production logging. "
        "Add it to your requirements."
    )