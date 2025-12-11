"""
Tests for the key search functionality in Django Cache Panel.

These tests verify the key search view behavior from end to end,
ensuring the full request/response cycle works correctly.
"""

from django.core.cache import caches
from django.urls import reverse

from .base import CacheTestCase


class TestKeySearchView(CacheTestCase):
    """Test cases for key search view."""

    def test_key_search_view_loads(self):
        """Test that the key search view loads for a valid cache."""
        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "default")
        self.assertContains(response, "Search Keys")

    def test_key_search_shows_cache_backend(self):
        """Test that the key search view shows the cache backend."""
        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = self.client.get(url)

        self.assertContains(response, "LocMemCache")

    def test_key_search_lists_all_keys_with_empty_query(self):
        """Test that searching with no query lists all keys."""
        cache = caches["default"]
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = self.client.get(url, {"q": ""})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "key1")
        self.assertContains(response, "key2")
        self.assertContains(response, "key3")

    def test_key_search_with_wildcard_pattern(self):
        """Test searching for keys with a wildcard pattern."""
        cache = caches["default"]
        cache.set("test:key1", "value1")
        cache.set("test:key2", "value2")
        cache.set("other:key", "value3")

        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = self.client.get(url, {"q": "test:*"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test:key1")
        self.assertContains(response, "test:key2")
        self.assertNotContains(response, "other:key")

    def test_key_search_exact_match(self):
        """Test exact key lookup shows the key and value."""
        cache = caches["default"]
        cache.set("exact:match:key", "exact_value")

        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = self.client.get(url, {"q": "exact:match:key"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "exact:match:key")
        self.assertContains(response, "exact_value")

    def test_key_search_no_results(self):
        """Test that searching for non-existent keys shows no results message."""
        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = self.client.get(url, {"q": "nonexistent:key:pattern:*"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No keys found")

    def test_key_search_pagination(self):
        """Test that pagination works when there are many keys."""
        cache = caches["default"]
        # Create more keys than per_page default
        for i in range(30):
            cache.set(f"paginate:key{i:02d}", f"value{i}")

        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = self.client.get(url, {"q": "paginate:*", "per_page": "10"})

        self.assertEqual(response.status_code, 200)
        # Should show pagination info
        self.assertContains(response, "Found 30 keys")
        # Should have next page link
        self.assertContains(response, "next")

    def test_key_search_pagination_page_2(self):
        """Test navigating to page 2 of results."""
        cache = caches["default"]
        for i in range(30):
            cache.set(f"page:key{i:02d}", f"value{i}")

        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = self.client.get(url, {"q": "page:*", "per_page": "10", "page": "2"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "showing 11 to 20")

    def test_key_search_per_page_option(self):
        """Test that per_page option is respected."""
        cache = caches["default"]
        for i in range(50):
            cache.set(f"perpage:key{i:02d}", f"value{i}")

        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = self.client.get(url, {"q": "perpage:*", "per_page": "25"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "showing 1 to 25")

    def test_key_search_unauthenticated(self):
        """Test that unauthenticated users cannot access key search."""
        client = self.create_unauthenticated_client()
        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_key_search_shows_value_preview(self):
        """Test that the search results show a value preview."""
        cache = caches["default"]
        cache.set("preview:key", "This is a test value for preview")

        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = self.client.get(url, {"q": "preview:*"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This is a test value for preview")


class TestIndexView(CacheTestCase):
    """Test cases for the index view cache list."""

    def test_index_has_clickable_cache_names(self):
        """Test that the index page has clickable cache name links."""
        url = reverse("dj_cache_panel:index")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Check that there's a link to the key search for default cache
        key_search_url = reverse("dj_cache_panel:key_search", args=["default"])
        self.assertContains(response, f'href="{key_search_url}"')

    def test_index_shows_all_configured_caches(self):
        """Test that the index shows all caches from settings."""
        url = reverse("dj_cache_panel:index")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Our test settings have 'default' and 'secondary' caches
        self.assertContains(response, "default")
        self.assertContains(response, "secondary")

    def test_index_links_to_correct_cache(self):
        """Test that each cache name links to its own key search."""
        url = reverse("dj_cache_panel:index")
        response = self.client.get(url)

        # Verify both caches have their own links
        default_url = reverse("dj_cache_panel:key_search", args=["default"])
        secondary_url = reverse("dj_cache_panel:key_search", args=["secondary"])

        self.assertContains(response, f'href="{default_url}"')
        self.assertContains(response, f'href="{secondary_url}"')
