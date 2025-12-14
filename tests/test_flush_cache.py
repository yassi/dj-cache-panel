"""
Tests for cache flush functionality.
"""

from django.urls import reverse
from django.core.cache import caches
from .base import CacheTestCase, OPERATIONAL_CACHES


class TestFlushCache(CacheTestCase):
    """Test cache flush functionality through the view layer."""

    def test_flush_cache_removes_all_keys(self):
        """Test that flushing a cache removes all keys."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Add some test keys
                cache.set("test_key_1", "value_1", timeout=300)
                cache.set("test_key_2", "value_2", timeout=300)
                cache.set("test_key_3", "value_3", timeout=300)

                # Verify keys exist
                self.assertEqual(cache.get("test_key_1"), "value_1")
                self.assertEqual(cache.get("test_key_2"), "value_2")
                self.assertEqual(cache.get("test_key_3"), "value_3")

                # Flush the cache via POST
                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.post(url, {"action": "flush"})

                # Should redirect back to key_search
                self.assertEqual(response.status_code, 302)
                self.assertIn(url, response.url)

                # Verify keys are gone
                self.assertIsNone(cache.get("test_key_1"))
                self.assertIsNone(cache.get("test_key_2"))
                self.assertIsNone(cache.get("test_key_3"))

    def test_flush_cache_shows_success_message(self):
        """Test that flushing shows a success message."""
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]

                # Add a test key
                cache.set("test_key", "test_value", timeout=300)

                # Flush the cache
                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.post(url, {"action": "flush"}, follow=True)

                # Check for success message
                self.assertEqual(response.status_code, 200)
                messages = list(response.context["messages"])
                self.assertTrue(
                    any(
                        "success" in str(m).lower() or "flush" in str(m).lower()
                        for m in messages
                    )
                )

    def test_flush_cache_requires_authentication(self):
        """Test that flush requires authentication."""
        # Logout
        self.client.logout()

        url = reverse("dj_cache_panel:key_search", args=["locmem"])
        response = self.client.post(url, {"action": "flush"})

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_flush_disabled_cache_shows_error(self):
        """Test that flushing a cache with flush disabled shows appropriate behavior."""
        # Dummy cache has flush_cache=False
        cache = caches["dummy"]

        # Try to flush
        url = reverse("dj_cache_panel:key_search", args=["dummy"])
        response = self.client.post(url, {"action": "flush"})

        # The view checks flush_supported before processing, so it won't redirect
        # It will just return the page with no action taken
        self.assertEqual(response.status_code, 200)
