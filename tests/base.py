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
    }
)
class CacheTestCase(TestCase):
    """
    Base test class for Django Cache Panel tests.

    Provides common setup for:
    - Test user creation (admin user)
    - Authenticated test client
    - Cache configuration via Django settings
    """

    def setUp(self):
        """Set up test data before each test."""
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

    def create_unauthenticated_client(self):
        """Create an unauthenticated Django test client."""
        return Client()
