"""
Pytest configuration for Django Cache Panel tests.

This configuration enables pytest-django to work with Django TestCase classes.
"""

import os
import sys
import django
from django.conf import settings


def pytest_configure(config):
    """Configure Django for pytest."""
    # Add the example_project directory to Python path for Django settings
    example_project_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "example_project"
    )
    if example_project_path not in sys.path:
        sys.path.insert(0, example_project_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example_project.settings")

    if not settings.configured:
        django.setup()

    # Override database settings based on TEST_DB_BACKEND environment variable
    test_db_backend = os.environ.get("TEST_DB_BACKEND", "postgresql").lower()

    if test_db_backend == "postgresql":
        # Configure PostgreSQL database
        postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
        postgres_port = os.environ.get("POSTGRES_PORT", "5432")
        postgres_user = os.environ.get("POSTGRES_USER", "postgres")
        postgres_password = os.environ.get("POSTGRES_PASSWORD", "postgres")
        postgres_db = os.environ.get("POSTGRES_DB", "postgres")

        settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": postgres_db,
                "USER": postgres_user,
                "PASSWORD": postgres_password,
                "HOST": postgres_host,
                "PORT": postgres_port,
            }
        }
    # else: use the default SQLite configuration from settings
