# """
# Development settings for instaAutoAI.
# """

# from .base import *  # noqa

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True

# ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# # Use SQLite for local development
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

# # Disable HTTPS requirements
# SECURE_SSL_REDIRECT = False
# SESSION_COOKIE_SECURE = False
# CSRF_COOKIE_SECURE = False

# # Email backend for development (console)
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# # Add django_extensions if installed
# try:
#     import django_extensions  # noqa

#     INSTALLED_APPS += ["django_extensions"]
# except ImportError:
#     pass

# # Enable WhiteNoise for realistic static file serving
# INSTALLED_APPS += ["whitenoise.runserver_nostatic"]

# # Log to console
# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {
#         "console": {
#             "class": "logging.StreamHandler",
#         },
#     },
#     "root": {
#         "handlers": ["console"],
#         "level": "INFO",
#     },
# }






















"""
Development settings for instaAutoAI.
"""

from .base import *  # noqa

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Use SQLite for local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Disable HTTPS requirements
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email backend for development (console)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Add django_extensions if installed
try:
    import django_extensions  # noqa

    INSTALLED_APPS += ["django_extensions"]
except ImportError:
    pass

# REMOVED: WhiteNoise already in base.py
# INSTALLED_APPS += ["whitenoise.runserver_nostatic"]

# Log to console
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}