"""
Base test class for Django Cache Panel tests.

This module provides a base test class with common setup for testing
the Django Cache Panel admin integration.
"""

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
        "secondary": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        },
        "database": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "test_cache_table",
        },
        "dummy": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        },
    }
)
class CacheTestCase(TestCase):
    """
    Base test class for Django Cache Panel tests.

    Provides common setup for:
    - Test user creation (admin user)
    - Authenticated test client
    - Cache configuration via Django settings
    - Multiple cache backends for comprehensive testing
    """

    # Define which caches support querying (listing keys with wildcards)
    QUERY_SUPPORTED_CACHES = ["default", "secondary", "database"]
    # Define which caches don't support querying
    NON_QUERY_CACHES = ["dummy"]

    def setUp(self):
        """Set up test data before each test."""
        # Create the database cache table
        from django.core.management import call_command

        try:
            call_command("createcachetable", "test_cache_table", verbosity=0)
        except Exception:
            # Table might already exist
            pass

        # Clear caches before each test
        from django.core.cache import caches

        for cache_name in ["default", "secondary", "database"]:
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
        self.client = Client()
        self.client.login(username="admin", password="testpass123")

    def tearDown(self):
        """Clean up after each test."""
        # Clear caches after each test
        from django.core.cache import caches

        for cache_name in ["default", "secondary", "database"]:
            try:
                caches[cache_name].clear()
            except Exception:
                pass

        # Drop the database cache table
        from django.db import connection

        try:
            with connection.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS test_cache_table")
        except Exception:
            pass

    def create_unauthenticated_client(self):
        """Create an unauthenticated Django test client."""
        return Client()
