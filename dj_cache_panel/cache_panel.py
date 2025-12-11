import fnmatch
from django.conf import settings
from django.core.cache import caches


# Mapping of backend class paths to panel classes
BACKEND_PANEL_MAP = {
    # Local memory cache
    "django.core.cache.backends.locmem.LocMemCache": "LocalMemoryCachePanel",
    # Redis backends
    "django.core.cache.backends.redis.RedisCache": "RedisCachePanel",
    "django_redis.cache.RedisCache": "RedisCachePanel",
    # Memcached backends
    "django.core.cache.backends.memcached.PyMemcacheCache": "MemcachedCachePanel",
    "django.core.cache.backends.memcached.PyLibMCCache": "MemcachedCachePanel",
    "django.core.cache.backends.memcached.MemcachedCache": "MemcachedCachePanel",
    # Database cache
    "django.core.cache.backends.db.DatabaseCache": "DatabaseCachePanel",
    # File-based cache
    "django.core.cache.backends.filebased.FileBasedCache": "FileBasedCachePanel",
    # Dummy cache
    "django.core.cache.backends.dummy.DummyCache": "DummyCachePanel",
}


def get_cache_panel(cache_name: str):
    """
    Returns the proper CachePanel subclass for the given cache name. This function
    inspects the cache configuration and returns the appropriate subclass.
    """
    cache_config = settings.CACHES.get(cache_name)
    if not cache_config:
        raise ValueError(f"Cache '{cache_name}' is not configured in CACHES setting.")

    backend = cache_config.get("BACKEND", "")

    panel_class_name = BACKEND_PANEL_MAP.get(backend)
    if panel_class_name:
        # Get the class from this module's globals
        panel_class = globals().get(panel_class_name)
        if panel_class:
            return panel_class(cache_name)

    # Fallback to a generic panel for unknown backends
    return GenericCachePanel(cache_name)


class CachePanel:
    """
    Defines the interface for a cache panel. An subclass of this is used to
    implement the cache panel for a specific cache backend.

    CachePanel subclasses are meant to feed presentation level data to a calling
    view. They are not meant to be used to modify the cache itself.
    """

    ABILITIES = {
        "query": False,
        "get_key": False,
        "delete_key": False,
        "flush_cache": False,
    }

    def __init__(self, cache_name: str):
        self.cache_name = cache_name

    @property
    def cache(self):
        """
        Returns the cache instance for the cache panel.
        """
        return caches[self.cache_name]

    @property
    def abilities(self):
        """
        Returns the abilities of the cache panel.
        """
        return self.ABILITIES

    def is_feature_supported(self, feature: str):
        """
        Returns True if the cache panel supports the given feature.
        """
        return self.abilities.get(feature, False)

    @property
    def _get_all_keys(self):
        """
        Convenience method to get all keys from the cache. This should be used for more
        basic backends like local memory.
        """
        return self.cache.keys("*")

    def _scan_keys(
        self,
        pattern: str = "*",
        page: int = 1,
        per_page: int = 25,
        scan_count: int = 100,
    ):
        """
        Scan the cache for keys and handle pagination.
        """
        keys = self.cache.keys(pattern)
        total_count = len(keys)
        keys = keys[(page - 1) * per_page : page * per_page]
        return {
            "keys": keys,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
        }

    def query(
        self,
        instance_alias: str,
        pattern: str = "*",
        page: int = 1,
        per_page: int = 25,
        scan_count: int = 100,
    ):
        """
        Query the cache for keys and handle pagination.
        """
        if not self.is_feature_supported("query"):
            raise NotImplementedError(
                "Querying is not supported for this cache backend."
            )
        return self._scan_keys(pattern, page, per_page, scan_count)

    def get_key(self, key: str):
        value = self.cache.get(key)
        return {
            "key": key,
            "value": value,
        }

    def delete_key(self, key: str):
        self.cache.delete(key)
        return {
            "success": True,
            "error": None,
            "message": f"Key {key} deleted successfully.",
        }

    def flush_cache(self):
        self.cache.flush()
        return {
            "success": True,
            "error": None,
            "message": "Cache flushed successfully.",
        }


class LocalMemoryCachePanel(CachePanel):
    """
    Implements the cache panel for the local memory cache backend.

    The LocMemCache stores keys in an internal _cache dict. We access this
    to provide key listing functionality.
    """

    ABILITIES = {
        "query": True,
        "get_key": True,
        "delete_key": True,
        "flush_cache": True,
    }

    def _get_internal_cache(self):
        """
        Access the internal cache dictionary of LocMemCache.
        The LocMemCache uses self._cache as the storage dict.
        """
        return getattr(self.cache, "_cache", {})

    def _scan_keys(
        self,
        pattern: str = "*",
        page: int = 1,
        per_page: int = 25,
        scan_count: int = 100,
    ):
        """
        Scan the local memory cache for keys matching the pattern.
        """
        internal_cache = self._get_internal_cache()

        # Get all keys and filter by pattern
        # LocMemCache prefixes keys with the key_prefix, we need to handle that
        key_prefix = getattr(self.cache, "key_prefix", "")

        all_keys = []
        for internal_key in internal_cache.keys():
            # Internal keys are formatted as ":{version}:{key_prefix}{key}"
            # We extract the user-facing key
            parts = internal_key.split(":", 2)
            if len(parts) >= 3:
                user_key = parts[2]
                if key_prefix and user_key.startswith(key_prefix):
                    user_key = user_key[len(key_prefix) :]
                all_keys.append(user_key)
            else:
                all_keys.append(internal_key)

        # Filter by pattern using fnmatch
        if pattern and pattern != "*":
            matching_keys = [k for k in all_keys if fnmatch.fnmatch(k, pattern)]
        else:
            matching_keys = all_keys

        # Sort for consistent ordering
        matching_keys.sort()

        total_count = len(matching_keys)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_keys = matching_keys[start_idx:end_idx]

        return {
            "keys": paginated_keys,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
        }

    def get_key(self, key: str):
        """
        Get a key value from the cache.
        """
        value = self.cache.get(key)
        exists = value is not None or self._key_exists(key)
        return {
            "key": key,
            "value": value,
            "exists": exists,
            "type": type(value).__name__ if value is not None else None,
        }

    def _key_exists(self, key: str):
        """
        Check if a key exists in the cache (handles None values).
        """
        # Use a sentinel to distinguish between "key not found" and "value is None"
        sentinel = object()
        return self.cache.get(key, sentinel) is not sentinel


class RedisCachePanel(CachePanel):
    """
    Implements the cache panel for the redis cache backend.
    """

    ABILITIES = {
        "query": False,
        "get_key": True,
        "delete_key": True,
        "flush_cache": True,
    }


class MemcachedCachePanel(CachePanel):
    """
    Implements the cache panel for the memcached cache backend.
    """

    ABILITIES = {
        "query": False,
        "get_key": True,
        "delete_key": True,
        "flush_cache": True,
    }


class DatabaseCachePanel(CachePanel):
    """
    Implements the cache panel for the database cache backend.
    """

    ABILITIES = {
        "query": False,
        "get_key": True,
        "delete_key": True,
        "flush_cache": True,
    }


class FileBasedCachePanel(CachePanel):
    """
    Implements the cache panel for the file based cache backend.
    """

    ABILITIES = {
        "query": False,
        "get_key": True,
        "delete_key": True,
        "flush_cache": True,
    }


class DummyCachePanel(CachePanel):
    """
    Implements the cache panel for the dummy cache backend.
    """

    ABILITIES = {
        "query": False,
        "get_key": True,
        "delete_key": True,
        "flush_cache": True,
    }


class GenericCachePanel(CachePanel):
    """
    A generic cache panel for unknown/unsupported cache backends.

    Provides basic get_key functionality but no query support.
    This serves as a fallback when no specific panel is available.
    """

    ABILITIES = {
        "query": False,
        "get_key": True,
        "delete_key": True,
        "flush_cache": False,
    }
