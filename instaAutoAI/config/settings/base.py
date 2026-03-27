"""
Base settings shared by all environments.
Uses django-environ to load configuration from environment variables or .env file.
"""

from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize environ
env = environ.Env(
    # set casting, default values
    DEBUG=(bool, False),
    SECRET_KEY=(str, ""),
    ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(str, f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
    REDIS_URL=(str, "redis://localhost:6379/0"),
    CELERY_BROKER_URL=(str, "redis://localhost:6379/0"),
    CELERY_RESULT_BACKEND=(str, "redis://localhost:6379/1"),
    OPENAI_API_KEY=(str, ""),
    SERPER_API_KEY=(str, ""),
    OLLAMA_BASE_URL=(str, "http://localhost:11434/v1"),
    OLLAMA_MODEL=(str, "qwen3:8b"),
    OLLAMA_NUM_CTX=(int, 4096),
    COMFYUI_URL=(str, "http://localhost:8188"),
    COMFYUI_OUTPUT_DIR=(str, ""),
    LANGGRAPH_CHECKPOINT_DB=(str, str(BASE_DIR / "checkpoints" / "langgraph.sqlite")),
    VRAM_LOCK_TTL=(int, 3600),
    AGENT_CONFIG_DIR=(str, str(BASE_DIR / "workflows")),
)

# Read .env file if it exists
environ.Env.read_env(BASE_DIR / ".env")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",  # for development static file serving
    "django.contrib.staticfiles",
    # Third party apps
    "rest_framework",
    "channels",
    "django_filters",
    # Local apps
    "apps.jobs",
    "apps.pipeline",
    "apps.users",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # after security, before everything else
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    "default": env.db(),
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Simplified static file serving.
# https://whitenoise.readthedocs.io/
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files (user uploaded content)
MEDIA_URL = "/media/"
MEDIA_ROOT = env("MEDIA_ROOT", default=str(BASE_DIR / "media"))

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# CRITICAL: Custom User Model Configuration
# This MUST be set to prevent auth.User and users.User clashes
AUTH_USER_MODEL = "users.User"  # Format: "app_label.ModelName"

# The app_label is determined by the AppsConfig in apps/users/apps.py
# which has: name = "apps.users" → app_label = "users" 


# Celery Configuration
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL")],
        },
    },
}

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "instaAutoAI.apps.jobs.pagination.JobPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
}

# Multi-Agent Framework Settings
OPENAI_API_KEY = env("OPENAI_API_KEY")
SERPER_API_KEY = env("SERPER_API_KEY")
OLLAMA_BASE_URL = env("OLLAMA_BASE_URL")
OLLAMA_MODEL = env("OLLAMA_MODEL")
OLLAMA_NUM_CTX = env("OLLAMA_NUM_CTX")

COMFYUI_URL = env("COMFYUI_URL")
COMFYUI_OUTPUT_DIR = env("COMFYUI_OUTPUT_DIR")

LANGGRAPH_CHECKPOINT_DB = env("LANGGRAPH_CHECKPOINT_DB")
AGENT_CONFIG_DIR = env("AGENT_CONFIG_DIR")
VRAM_LOCK_TTL = env("VRAM_LOCK_TTL")