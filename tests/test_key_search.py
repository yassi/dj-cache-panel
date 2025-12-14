"""
Tests for the key search functionality in Django Cache Panel.

These tests verify the key search view behavior from end to end,
ensuring the full request/response cycle works correctly.

Tests are run against multiple cache backends to ensure compatibility.
"""

from django.core.cache import caches
from django.urls import reverse

from .base import CacheTestCase, QUERY_SUPPORTED_CACHES, NON_QUERY_CACHES


class TestKeySearchView(CacheTestCase):
    """Test cases for key search view across all cache backends."""

    def test_key_search_view_loads(self):
        """Test that the key search view loads for all cache backends."""
        for cache_name in QUERY_SUPPORTED_CACHES + NON_QUERY_CACHES:
            with self.subTest(cache=cache_name):
                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, cache_name)
                self.assertContains(response, "Key Search")

    def test_key_search_shows_cache_backend(self):
        """Test that the key search view shows the cache backend type."""
        backend_names = {
            "default": "LocMemCache",
            "locmem": "LocMemCache",
            "database": "DatabaseCache",
            "filesystem": "FileBasedCache",
            "dummy": "DummyCache",
        }
        for cache_name, backend_name in backend_names.items():
            with self.subTest(cache=cache_name):
                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.get(url)

                self.assertContains(response, backend_name)

    def test_key_search_lists_all_keys_with_empty_query(self):
        """Test that searching with no query lists all keys (for query-supported caches)."""
        for cache_name in QUERY_SUPPORTED_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]
                cache.set("key1", "value1")
                cache.set("key2", "value2")
                cache.set("key3", "value3")

                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.get(url, {"q": ""})

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "key1")
                self.assertContains(response, "key2")
                self.assertContains(response, "key3")

    def test_key_search_with_wildcard_pattern(self):
        """Test searching for keys with a wildcard pattern across all query-supported caches."""
        for cache_name in QUERY_SUPPORTED_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]
                cache.set("test:key1", "value1")
                cache.set("test:key2", "value2")
                cache.set("other:key", "value3")

                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.get(url, {"q": "test:*"})

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "test:key1")
                self.assertContains(response, "test:key2")
                self.assertNotContains(response, "other:key")

    def test_key_search_exact_match(self):
        """Test exact key lookup shows the key for query-supported caches."""
        for cache_name in QUERY_SUPPORTED_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]
                cache.set("exact:match:key", "exact_value", timeout=300)

                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.get(url, {"q": "exact:match:key"})

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "exact:match:key")
                # Note: Value preview was removed from key search page

    def test_key_search_no_results(self):
        """Test that searching for non-existent keys shows no results message."""
        for cache_name in QUERY_SUPPORTED_CACHES:
            with self.subTest(cache=cache_name):
                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.get(url, {"q": "nonexistent:key:pattern:*"})

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "No keys found")

    def test_key_search_pagination(self):
        """Test that pagination works when there are many keys."""
        for cache_name in QUERY_SUPPORTED_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]
                # Create more keys than per_page default
                for i in range(30):
                    cache.set(f"paginate{cache_name}:key{i:02d}", f"value{i}")

                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.get(
                    url, {"q": f"paginate{cache_name}:*", "per_page": "10"}
                )

                self.assertEqual(response.status_code, 200)
                # Should show pagination info
                self.assertContains(response, "Found 30 keys")
                # Should have next page link
                self.assertContains(response, "next")

    def test_key_search_pagination_page_2(self):
        """Test navigating to page 2 of results."""
        for cache_name in QUERY_SUPPORTED_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]
                for i in range(30):
                    cache.set(f"page{cache_name}:key{i:02d}", f"value{i}")

                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.get(
                    url,
                    {"q": f"page{cache_name}:*", "per_page": "10", "page": "2"},
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "showing 11 to 20")

    def test_key_search_per_page_option(self):
        """Test that per_page option is respected."""
        for cache_name in QUERY_SUPPORTED_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]
                for i in range(50):
                    cache.set(f"perpage{cache_name}:key{i:02d}", f"value{i}")

                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.get(
                    url, {"q": f"perpage{cache_name}:*", "per_page": "25"}
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "showing 1 to 25")

    def test_key_search_unauthenticated(self):
        """Test that unauthenticated users cannot access key search."""
        from django.test import Client

        client = Client()
        url = reverse("dj_cache_panel:key_search", args=["default"])
        response = client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_key_search_shows_keys(self):
        """Test that the search results show keys (value preview was removed)."""
        for cache_name in QUERY_SUPPORTED_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]
                cache.set("preview:key", "This is a test value for preview")

                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.get(url, {"q": "preview:*"})

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "preview:key")

    def test_key_search_non_query_cache_shows_message(self):
        """Test that non-query caches show appropriate messaging."""
        for cache_name in NON_QUERY_CACHES:
            with self.subTest(cache=cache_name):
                url = reverse("dj_cache_panel:key_search", args=[cache_name])
                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)
                # Should show message about key listing or searching not being supported
                # Different backends may show different messages
                # Just verify the page loads and shows the cache name
                self.assertContains(response, cache_name)


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
        # Our test settings have multiple caches
        self.assertContains(response, "default")
        self.assertContains(response, "locmem")
        self.assertContains(response, "database")
        self.assertContains(response, "filesystem")
        self.assertContains(response, "dummy")

    def test_index_links_to_correct_cache(self):
        """Test that each cache name links to its own key search."""
        url = reverse("dj_cache_panel:index")
        response = self.client.get(url)

        # Verify caches have their own links
        default_url = reverse("dj_cache_panel:key_search", args=["default"])
        locmem_url = reverse("dj_cache_panel:key_search", args=["locmem"])

        self.assertContains(response, f'href="{default_url}"')
        self.assertContains(response, f'href="{locmem_url}"')

    def test_index_shows_abilities(self):
        """Test that the index page shows cache abilities."""
        url = reverse("dj_cache_panel:index")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Check that ability columns are present
        self.assertContains(response, "Query")
        self.assertContains(response, "Get")
        self.assertContains(response, "Delete")
        self.assertContains(response, "Flush")

        # Check that we have checkmarks and dashes (for supported/unsupported)
        self.assertContains(response, "✓")
        self.assertContains(response, "—")

    def test_index_shows_backend_info(self):
        """Test that the index page shows backend type for each cache."""
        url = reverse("dj_cache_panel:index")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Check for backend names (shortened versions)
        self.assertContains(response, "LocMemCache")
        self.assertContains(response, "DatabaseCache")
        self.assertContains(response, "FileBasedCache")
        self.assertContains(response, "DummyCache")
