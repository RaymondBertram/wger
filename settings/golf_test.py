"""Golf backend tests with an in-memory database and no deployment overrides."""

# ruff: noqa: F403, F405

# wger
from .ci import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {'NAME': ':memory:', 'MIGRATE': False},
    }
}
MEDIA_ROOT = BASE_DIR.parent / '.cache' / 'test-media'
