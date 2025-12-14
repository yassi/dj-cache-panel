"""
Tests for deleting cache keys.
"""

from django.urls import reverse
from django.core.cache import caches
from .base import CacheTestCase, OPERATIONAL_CACHES
from urllib.parse import quote


class TestDeleteKey(CacheTestCase):
    """Test deleting keys through the view layer."""

    def test_delete_existing_key(self):
        """Test deleting an existing key."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Create a key
                cache.set("delete_test_key", "test_value", timeout=300)

                # Verify key exists
                self.assertEqual(cache.get("delete_test_key"), "test_value")

                # Delete the key via POST
                url = reverse(
                    "dj_cache_panel:key_detail",
                    args=[cache_name, quote("delete_test_key")],
                )
                response = self.client.post(
                    url,
                    {
                        "action": "delete",
                    },
                )

                # Should redirect to key_search
                self.assertEqual(response.status_code, 302)
                self.assertIn(f"/admin/dj-cache-panel/{cache_name}/keys/", response.url)

                # Verify key is gone
                self.assertIsNone(cache.get("delete_test_key"))

    def test_delete_shows_success_message(self):
        """Test that deleting shows a success message."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Create a key
                cache.set("message_delete_key", "test_value", timeout=300)

                # Delete the key
                url = reverse(
                    "dj_cache_panel:key_detail",
                    args=[cache_name, quote("message_delete_key")],
                )
                response = self.client.post(
                    url,
                    {
                        "action": "delete",
                    },
                    follow=True,
                )

                self.assertEqual(response.status_code, 200)
                messages = list(response.context["messages"])
                self.assertTrue(
                    any(
                        "success" in str(m).lower() or "deleted" in str(m).lower()
                        for m in messages
                    )
                )

    def test_delete_requires_authentication(self):
        """Test that deleting requires authentication."""
        cache = caches["locmem"]
        cache.set("auth_delete_key", "value", timeout=300)

        self.client.logout()

        url = reverse(
            "dj_cache_panel:key_detail", args=["locmem", quote("auth_delete_key")]
        )
        response = self.client.post(
            url,
            {
                "action": "delete",
            },
        )

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

        # Verify key still exists
        self.assertEqual(cache.get("auth_delete_key"), "value")

    def test_delete_nonexistent_key_handles_gracefully(self):
        """Test that deleting a non-existent key handles gracefully."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Ensure key doesn't exist
                cache.delete("nonexistent_delete_key")

                # Try to delete non-existent key
                url = reverse(
                    "dj_cache_panel:key_detail",
                    args=[cache_name, quote("nonexistent_delete_key")],
                )
                response = self.client.post(
                    url,
                    {
                        "action": "delete",
                    },
                )

                # Should still redirect (delete is idempotent)
                self.assertEqual(response.status_code, 302)

    def test_delete_key_with_special_characters(self):
        """Test deleting a key with special characters in the name."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Create key with special characters
                special_key = "test:key:with:colons"
                cache.set(special_key, "test_value", timeout=300)

                # Verify key exists
                self.assertEqual(cache.get(special_key), "test_value")

                # Delete the key
                url = reverse(
                    "dj_cache_panel:key_detail", args=[cache_name, quote(special_key)]
                )
                response = self.client.post(
                    url,
                    {
                        "action": "delete",
                    },
                )

                self.assertEqual(response.status_code, 302)

                # Verify key is gone
                self.assertIsNone(cache.get(special_key))

    def test_delete_multiple_keys_sequentially(self):
        """Test deleting multiple keys one after another."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Create multiple keys
                cache.set("delete_key_1", "value_1", timeout=300)
                cache.set("delete_key_2", "value_2", timeout=300)
                cache.set("delete_key_3", "value_3", timeout=300)

                # Delete each key
                for i in range(1, 4):
                    key = f"delete_key_{i}"
                    url = reverse(
                        "dj_cache_panel:key_detail", args=[cache_name, quote(key)]
                    )
                    response = self.client.post(url, {"action": "delete"})
                    self.assertEqual(response.status_code, 302)
                    self.assertIsNone(cache.get(key))
