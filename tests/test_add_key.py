"""
Tests for adding cache keys.
"""

from django.urls import reverse
from django.core.cache import caches
from .base import CacheTestCase, OPERATIONAL_CACHES
import json


class TestAddKey(CacheTestCase):
    """Test adding new keys through the view layer."""

    def test_add_simple_string_key(self):
        """Test adding a simple string key."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Add a key via POST
                url = reverse("dj_cache_panel:key_add", args=[cache_name])
                response = self.client.post(
                    url,
                    {
                        "key": "new_test_key",
                        "value": "new_test_value",
                    },
                )

                # Should redirect to key_search
                self.assertEqual(response.status_code, 302)
                self.assertIn(f"/admin/dj-cache-panel/{cache_name}/keys/", response.url)

                # Verify key was created
                self.assertEqual(cache.get("new_test_key"), "new_test_value")

    def test_add_json_value(self):
        """Test adding a key with JSON value."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Add a key with JSON value
                json_value = json.dumps({"name": "test", "count": 42})
                url = reverse("dj_cache_panel:key_add", args=[cache_name])
                response = self.client.post(
                    url,
                    {
                        "key": "json_key",
                        "value": json_value,
                    },
                )

                self.assertEqual(response.status_code, 302)

                # Verify key was created with parsed JSON
                stored_value = cache.get("json_key")
                self.assertIsInstance(stored_value, dict)
                self.assertEqual(stored_value["name"], "test")
                self.assertEqual(stored_value["count"], 42)

    def test_add_key_with_timeout(self):
        """Test adding a key with a custom timeout."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Add a key with timeout
                url = reverse("dj_cache_panel:key_add", args=[cache_name])
                response = self.client.post(
                    url,
                    {
                        "key": "timeout_key",
                        "value": "timeout_value",
                        "timeout": "60",
                    },
                )

                self.assertEqual(response.status_code, 302)

                # Verify key exists
                self.assertEqual(cache.get("timeout_key"), "timeout_value")

    def test_add_key_shows_success_message(self):
        """Test that adding a key shows a success message."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                url = reverse("dj_cache_panel:key_add", args=[cache_name])
                response = self.client.post(
                    url,
                    {
                        "key": "message_test_key",
                        "value": "message_test_value",
                    },
                    follow=True,
                )

                self.assertEqual(response.status_code, 200)
                messages = list(response.context["messages"])
                self.assertTrue(
                    any(
                        "success" in str(m).lower() or "created" in str(m).lower()
                        for m in messages
                    )
                )

    def test_add_key_requires_authentication(self):
        """Test that adding a key requires authentication."""
        self.client.logout()

        url = reverse("dj_cache_panel:key_add", args=["locmem"])
        response = self.client.post(
            url,
            {
                "key": "test_key",
                "value": "test_value",
            },
        )

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_add_key_get_shows_form(self):
        """Test that GET request shows the add key form."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                url = reverse("dj_cache_panel:key_add", args=[cache_name])
                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Add New Key")
                self.assertContains(response, cache_name)

    def test_add_duplicate_key_overwrites(self):
        """Test that adding a duplicate key overwrites the existing value."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Set initial value
                cache.set("duplicate_key", "original_value", timeout=300)

                # Add same key with new value
                url = reverse("dj_cache_panel:key_add", args=[cache_name])
                response = self.client.post(
                    url,
                    {
                        "key": "duplicate_key",
                        "value": "new_value",
                    },
                )

                self.assertEqual(response.status_code, 302)

                # Verify value was overwritten
                self.assertEqual(cache.get("duplicate_key"), "new_value")
