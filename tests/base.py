"""
Base test class for dj-cache-panel tests.
"""

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from pathlib import Path
import tempfile
import os


User = get_user_model()


# Base directory for tests
TEST_DIR = Path(__file__).resolve().parent

# Temporary directory for file-based cache during tests
FILE_BASED_CACHE_DIR = tempfile.mkdtemp(prefix="dj_cache_panel_test_")

# Environment variables for external services
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = os.environ.get("REDIS_PORT", "6379")
MEMCACHED_HOST = os.environ.get("MEMCACHED_HOST", "localhost")
MEMCACHED_PORT = os.environ.get("MEMCACHED_PORT", "11211")

# Define cache configurations for testing
# Redis and Memcached are assumed to be available
TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "default-test-cache",
    },
    "locmem": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "locmem-test-cache",
    },
    "database": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "test_cache_table",
    },
    "filesystem": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": FILE_BASED_CACHE_DIR,
    },
    "dummy": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
    "redis": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
    },
    "django_redis": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
    "memcached": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": f"{MEMCACHED_HOST}:{MEMCACHED_PORT}",
    },
}

# Categorize caches by their query support
QUERY_SUPPORTED_CACHES = ["locmem", "database", "redis", "django_redis"]
NON_QUERY_CACHES = ["dummy", "filesystem", "memcached"]

# All caches that support basic operations (get, set, delete)
OPERATIONAL_CACHES = [
    "locmem",
    "database",
    "filesystem",
    "redis",
    "django_redis",
    "memcached",
]


@override_settings(CACHES=TEST_CACHES)
class CacheTestCase(TestCase):
    """
    Base test class for Django Cache Panel tests.

    Provides common setup for:
    - Test user creation (admin user)
    - Authenticated test client
    - Cache configuration via Django settings
    - Multiple cache backends for comprehensive testing
    """

    def setUp(self):
        """Set up test data before each test."""
        from django.core.management import call_command
        from django.core.cache import caches
        import shutil

        # Create the database cache table
        try:
            call_command("createcachetable", "test_cache_table", verbosity=0)
        except Exception:
            # Table might already exist
            pass

        # Create filesystem cache directory
        if os.path.exists(FILE_BASED_CACHE_DIR):
            shutil.rmtree(FILE_BASED_CACHE_DIR)
        os.makedirs(FILE_BASED_CACHE_DIR, exist_ok=True)

        # Clear all caches before each test
        for cache_name in TEST_CACHES.keys():
            try:
                caches[cache_name].clear()
            except Exception:
                pass

        # Create admin user
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )

        # Create authenticated client
        self.client.login(username="admin", password="testpass123")

    def tearDown(self):
        """Clean up after each test."""
        from django.core.cache import caches
        from django.db import connection
        import shutil

        # Clear all caches after each test
        for cache_name in TEST_CACHES.keys():
            try:
                caches[cache_name].clear()
            except Exception:
                pass

        # Drop the database cache table
        try:
            with connection.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS test_cache_table")
        except Exception:
            pass

        # Clean up filesystem cache directory
        if os.path.exists(FILE_BASED_CACHE_DIR):
            try:
                shutil.rmtree(FILE_BASED_CACHE_DIR)
            except Exception:
                pass
