"""
Tests for editing/updating cache keys.
"""

from django.urls import reverse
from django.core.cache import caches
from .base import CacheTestCase, OPERATIONAL_CACHES
import json
from urllib.parse import quote


class TestEditKey(CacheTestCase):
    """Test editing existing keys through the view layer."""

    def test_edit_simple_string_value(self):
        """Test editing a simple string value."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Create initial key
                cache.set("edit_test_key", "original_value", timeout=300)

                # Edit the key via POST
                url = reverse(
                    "dj_cache_panel:key_detail",
                    args=[cache_name, quote("edit_test_key")],
                )
                response = self.client.post(
                    url,
                    {
                        "action": "update",
                        "value": "updated_value",
                    },
                )

                # Should redirect back to detail page
                self.assertEqual(response.status_code, 302)

                # Verify value was updated
                self.assertEqual(cache.get("edit_test_key"), "updated_value")

    def test_edit_json_value(self):
        """Test editing a JSON value."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Create initial key with dict value
                cache.set(
                    "json_edit_key", {"name": "original", "count": 1}, timeout=300
                )

                # Edit with new JSON
                new_json = json.dumps({"name": "updated", "count": 2})
                url = reverse(
                    "dj_cache_panel:key_detail",
                    args=[cache_name, quote("json_edit_key")],
                )
                response = self.client.post(
                    url,
                    {
                        "action": "update",
                        "value": new_json,
                    },
                )

                self.assertEqual(response.status_code, 302)

                # Verify value was updated
                stored_value = cache.get("json_edit_key")
                self.assertIsInstance(stored_value, dict)
                self.assertEqual(stored_value["name"], "updated")
                self.assertEqual(stored_value["count"], 2)

    def test_edit_with_timeout(self):
        """Test editing a key with a new timeout."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Create initial key
                cache.set("timeout_edit_key", "original", timeout=300)

                # Edit with new timeout
                url = reverse(
                    "dj_cache_panel:key_detail",
                    args=[cache_name, quote("timeout_edit_key")],
                )
                response = self.client.post(
                    url,
                    {
                        "action": "update",
                        "value": "updated",
                        "timeout": "120",
                    },
                )

                self.assertEqual(response.status_code, 302)

                # Verify value was updated
                self.assertEqual(cache.get("timeout_edit_key"), "updated")

    def test_edit_shows_success_message(self):
        """Test that editing shows a success message."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Create initial key
                cache.set("message_test_key", "original", timeout=300)

                # Edit the key
                url = reverse(
                    "dj_cache_panel:key_detail",
                    args=[cache_name, quote("message_test_key")],
                )
                response = self.client.post(
                    url,
                    {
                        "action": "update",
                        "value": "updated",
                    },
                    follow=True,
                )

                self.assertEqual(response.status_code, 200)
                messages = list(response.context["messages"])
                self.assertTrue(
                    any(
                        "success" in str(m).lower() or "updated" in str(m).lower()
                        for m in messages
                    )
                )

    def test_edit_requires_authentication(self):
        """Test that editing requires authentication."""
        cache = caches["locmem"]
        cache.set("auth_test_key", "value", timeout=300)

        self.client.logout()

        url = reverse(
            "dj_cache_panel:key_detail", args=["locmem", quote("auth_test_key")]
        )
        response = self.client.post(
            url,
            {
                "action": "update",
                "value": "new_value",
            },
        )

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_edit_nonexistent_key_shows_error(self):
        """Test that editing a non-existent key shows an error."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                url = reverse(
                    "dj_cache_panel:key_detail",
                    args=[cache_name, quote("nonexistent_key")],
                )
                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)
                # Should show error message about key not existing
                self.assertContains(response, "does not exist", status_code=200)

    def test_edit_key_with_special_characters(self):
        """Test editing a key with special characters in the name."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Create key with special characters
                special_key = "test:key:with:colons"
                cache.set(special_key, "original", timeout=300)

                # Edit the key
                url = reverse(
                    "dj_cache_panel:key_detail", args=[cache_name, quote(special_key)]
                )
                response = self.client.post(
                    url,
                    {
                        "action": "update",
                        "value": "updated",
                    },
                )

                self.assertEqual(response.status_code, 302)

                # Verify value was updated
                self.assertEqual(cache.get(special_key), "updated")

    def test_view_key_detail_get(self):
        """Test that GET request shows the key detail page."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Create a key
                cache.set("view_test_key", "test_value", timeout=300)

                # View the key
                url = reverse(
                    "dj_cache_panel:key_detail",
                    args=[cache_name, quote("view_test_key")],
                )
                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "view_test_key")
                self.assertContains(response, "test_value")
