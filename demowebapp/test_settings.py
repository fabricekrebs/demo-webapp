"""
Test settings for GitHub Actions CI
"""

import os

from .settings import *

# Override database settings for testing
if "CI" in os.environ or "GITHUB_ACTIONS" in os.environ:
    # Use the PostgreSQL service container in GitHub Actions
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "postgres",
            "USER": "testuser",
            "PASSWORD": "testpassword",
            "HOST": "localhost",
            "PORT": "5432",
        }
    }
else:
    # Use SQLite for local testing if PostgreSQL is not available
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test_db.sqlite3",
        }
    }

# Disable Azure Monitor in tests
ENABLE_AZURE_MONITOR = False

# Override Azure Monitor environment variables to prevent initialization
import os

os.environ["ENABLE_AZURE_MONITOR"] = "False"
os.environ.pop("APPLICATIONINSIGHTS_CONNECTION_STRING", None)

# Test-specific settings
DEBUG = False
SECRET_KEY = os.environ.get("SECRET_KEY", "test-secret-key-for-testing-only")  # nosec B105
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]


# Disable migrations for faster testing (optional)
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


# Uncomment the next line if you want to disable migrations for faster tests
# MIGRATION_MODULES = DisableMigrations()

# Use simple password hasher for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "propagate": False,
        },
    },
}

# Email backend for testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Cache for testing
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Media files for testing
MEDIA_ROOT = BASE_DIR / "test_media"

# Static files for testing
STATIC_ROOT = BASE_DIR / "test_static"
