"""Golf Training staging settings.

Domain: https://training.bertram-tech.de
Backend: 127.0.0.1:8002

Separate from the local development environment.
"""

# ruff: noqa: F403, F405

import os

from django.core.exceptions import ImproperlyConfigured

from .settings_global import *


# General
DEBUG = False

SECRET_KEY = os.environ.get("GOLF_STAGING_SECRET_KEY")

if not SECRET_KEY or len(SECRET_KEY) < 50:
    raise ImproperlyConfigured(
        "GOLF_STAGING_SECRET_KEY must contain at least 50 characters."
    )

ALLOWED_HOSTS = [
    "training.bertram-tech.de",
]

SITE_URL = "https://training.bertram-tech.de"

TIME_ZONE = "Europe/Berlin"


# Security
CSRF_TRUSTED_ORIGINS = [
    "https://training.bertram-tech.de",
]

CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = [
    "https://training.bertram-tech.de",
]

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

X_FRAME_OPTIONS = "DENY"

SECURE_CONTENT_TYPE_NOSNIFF = True


# Database
GOLF_STAGING_ROOT = BASE_DIR.parent / "db" / "golf-staging"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": GOLF_STAGING_ROOT / "database.sqlite3",
        "TEST": {
            "NAME": ":memory:",
        },
    }
}


# Media & Static
MEDIA_ROOT = GOLF_STAGING_ROOT / "media"
STATIC_ROOT = GOLF_STAGING_ROOT / "static"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "golf-training-staging",
        "TIMEOUT": 100,
    }
}


# Email
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_DELIVERY_BACKEND = EMAIL_BACKEND

DEFAULT_FROM_EMAIL = "Golf Training <noreply@example.invalid>"

ACCOUNT_EMAIL_VERIFICATION = "mandatory"


# Security Features
AXES_ENABLED = True
EXPOSE_PROMETHEUS_METRICS = False


# wger
WGER_SETTINGS = {
    **WGER_SETTINGS,
    "EMAIL_FROM": DEFAULT_FROM_EMAIL,
    "ALLOW_REGISTRATION": False,
    "ALLOW_GUEST_USERS": False,
    "ALLOW_UPLOAD_VIDEOS": False,
    "DOWNLOAD_INGREDIENTS_FROM": "None",
    "USE_CELERY": False,
    "USE_RECAPTCHA": False,
    "SYNC_EXERCISES_CELERY": False,
    "SYNC_EXERCISE_IMAGES_CELERY": False,
    "SYNC_EXERCISE_VIDEOS_CELERY": False,
    "SYNC_INGREDIENTS_CELERY": False,
    "SYNC_OFF_DAILY_DELTA_CELERY": False,
    "EXPORT_INGREDIENTS_BULK_CELERY": False,
    "CACHE_API_EXERCISES_CELERY": False,
    "CACHE_API_EXERCISES_CELERY_FORCE_UPDATE": False,
}