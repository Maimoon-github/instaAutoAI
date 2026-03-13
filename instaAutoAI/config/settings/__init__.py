"""
Settings loader that selects the appropriate configuration based on DJANGO_ENV.
Defaults to 'development' if the environment variable is not set.
"""
import os

from django.core.exceptions import ImproperlyConfigured

# Determine which settings module to use
DJANGO_ENV = os.getenv("DJANGO_ENV", "development").lower()

if DJANGO_ENV == "production":
    from .production import *  # noqa
elif DJANGO_ENV == "development":
    from .development import *  # noqa
else:
    raise ImproperlyConfigured(f"Unknown DJANGO_ENV: {DJANGO_ENV}. Use 'development' or 'production'.")

# Optional: Ensure DEBUG is not True in production
if DJANGO_ENV == "production" and DEBUG:  # noqa
    raise ImproperlyConfigured("Production environment must have DEBUG=False.")