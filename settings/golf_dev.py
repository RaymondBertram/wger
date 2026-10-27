"""Isolated, loopback-only Golf Training development settings.

Select explicitly with --settings=settings.golf_dev. Do not use for deployment.
This module intentionally imports neither production nor untracked local settings.
"""

# ruff: noqa: F403, F405

# wger
from .settings_global import *


DEBUG = True
# Public development-only value, never a deployment signing key.
SECRET_KEY = 'golf-training-loopback-development-only-not-for-production'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
SITE_URL = 'http://localhost:8001'
CSRF_TRUSTED_ORIGINS = ['http://localhost:8001', 'http://127.0.0.1:8001']
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS
TIME_ZONE = 'Europe/Berlin'

# Fixed project-local paths: deployment database/environment variables are ignored.
GOLF_DEV_ROOT = BASE_DIR.parent / 'db' / 'golf-dev'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': GOLF_DEV_ROOT / 'database.sqlite3',
        'TEST': {'NAME': ':memory:'},
    }
}
MEDIA_ROOT = GOLF_DEV_ROOT / 'media'
STATIC_ROOT = GOLF_DEV_ROOT / 'static'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'golf-training-development',
        'TIMEOUT': 100,
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_DELIVERY_BACKEND = EMAIL_BACKEND
DEFAULT_FROM_EMAIL = 'Golf Training Development <golf-dev@example.invalid>'
ACCOUNT_EMAIL_VERIFICATION = 'none'
AXES_ENABLED = False
EXPOSE_PROMETHEUS_METRICS = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

WGER_SETTINGS = {
    **WGER_SETTINGS,
    'EMAIL_FROM': DEFAULT_FROM_EMAIL,
    'ALLOW_REGISTRATION': True,
    'ALLOW_GUEST_USERS': False,
    'ALLOW_UPLOAD_VIDEOS': False,
    'DOWNLOAD_INGREDIENTS_FROM': 'None',
    'USE_CELERY': False,
    'USE_RECAPTCHA': False,
    'SYNC_EXERCISES_CELERY': False,
    'SYNC_EXERCISE_IMAGES_CELERY': False,
    'SYNC_EXERCISE_VIDEOS_CELERY': False,
    'SYNC_INGREDIENTS_CELERY': False,
    'SYNC_OFF_DAILY_DELTA_CELERY': False,
    'EXPORT_INGREDIENTS_BULK_CELERY': False,
    'CACHE_API_EXERCISES_CELERY': False,
    'CACHE_API_EXERCISES_CELERY_FORCE_UPDATE': False,
}
