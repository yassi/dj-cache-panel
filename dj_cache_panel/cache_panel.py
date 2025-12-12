import fnmatch
import time
from django.db import connection
from django.conf import settings
from django.core.cache import caches


# Default Mapping of backend class paths to panel classes
BACKEND_PANEL_MAP_DEFAULT = {
    # Local memory cache
    "django.core.cache.backends.locmem.LocMemCache": "LocalMemoryCachePanel",
    # Redis backends (standalone - cluster detection happens in get_cache_panel)
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

BACKEND_PANEL_MAP = getattr(
    settings, "DJ_CACHE_PANEL_BACKEND_PANEL_MAP", BACKEND_PANEL_MAP_DEFAULT
)


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


class DatabaseCachePanel(CachePanel):
    """
    Implements the cache panel for the database cache backend.

    The Django database cache backend stores cache entries in a database table
    with columns: cache_key, value, expires.
    """

    ABILITIES = {
        "query": True,
        "get_key": True,
        "delete_key": True,
        "flush_cache": True,
    }

    def _get_table_name(self):
        """
        Get the database table name for this cache.
        """
        return self.cache._table

    def _wildcard_to_sql_like(self, pattern: str):
        """
        Convert a wildcard pattern (e.g., 'test:*') to SQL LIKE pattern (e.g., 'test:%').
        Also escapes SQL special characters.
        """
        # Replace * with % for SQL LIKE
        sql_pattern = pattern.replace("*", "%").replace("?", "_")
        return sql_pattern

    def _scan_keys(
        self,
        pattern: str = "*",
        page: int = 1,
        per_page: int = 25,
        scan_count: int = 100,
    ):
        """
        Scan the database cache for keys matching the pattern.

        Uses raw SQL to query the cache table directly since Django's cache
        backend doesn't provide a model with proper field names.

        Note: Django's database cache backend applies a key prefix using the
        make_key() method, so raw keys are transformed before storage.
        """
        table_name = self._get_table_name()

        # Convert wildcard pattern to SQL LIKE pattern
        # Django's cache backend will transform keys using make_key(),
        # which adds version and key_prefix, so we need to match the transformed keys
        if pattern and pattern != "*":
            # Transform the pattern using the cache's make_key to match stored keys
            # For simple patterns, we'll do a substring match
            transformed_pattern = self.cache.make_key(pattern)
            # Replace the pattern's * with % for SQL LIKE
            sql_pattern = transformed_pattern.replace("*", "%").replace("?", "_")
        else:
            sql_pattern = "%"

        # Get current time as Unix timestamp
        # The database cache backend stores expires as a decimal/float timestamp
        current_time = time.time()

        # Query for keys that match the pattern and haven't expired
        with connection.cursor() as cursor:
            # Count total matching keys that haven't expired
            count_sql = f"""
                SELECT COUNT(*) 
                FROM {table_name} 
                WHERE cache_key LIKE %s AND expires > %s
            """
            cursor.execute(count_sql, [sql_pattern, current_time])
            total_count = cursor.fetchone()[0]

            # Get paginated keys
            start_idx = (page - 1) * per_page
            keys_sql = f"""
                SELECT cache_key 
                FROM {table_name}
                WHERE cache_key LIKE %s AND expires > %s
                ORDER BY cache_key
                LIMIT %s OFFSET %s
            """
            cursor.execute(keys_sql, [sql_pattern, current_time, per_page, start_idx])
            # Transform back from cache_key to the user-facing key
            raw_keys = [row[0] for row in cursor.fetchall()]

            # Reverse the make_key transformation to get original keys
            keys = []
            for cache_key in raw_keys:
                # The reverse transformation: remove version and key_prefix
                original_key = self.cache.key_prefix
                if cache_key.startswith(self.cache.key_prefix):
                    # Remove the prefix to get back to the original key
                    key_without_prefix = cache_key[len(self.cache.key_prefix) :]
                    # Remove version prefix (format is :VERSION:key)
                    parts = key_without_prefix.split(":", 2)
                    if len(parts) >= 3:
                        original_key = parts[2]
                    else:
                        original_key = key_without_prefix
                    keys.append(original_key)
                else:
                    keys.append(cache_key)

        return {
            "keys": keys,
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
        }


class FileBasedCachePanel(CachePanel):
    """
    Implements the cache panel for the file based cache backend.

    Note: Django's file-based cache stores keys as hashed filenames
    (e.g., '4a50768ddcc707351283f01376588f38.djcache'), making it
    impossible to list original key names without the keys themselves.
    Therefore, query support is disabled for this backend.
    """

    ABILITIES = {
        "query": False,  # Cannot list keys - they're stored as hashed filenames
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
        "get_key": False,
        "delete_key": False,
        "flush_cache": False,
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


class RedisCachePanel(CachePanel):
    """
    Implements the cache panel for standalone Redis instances.

    Uses the SCAN command to iterate through keys efficiently without
    blocking the Redis server.
    """

    ABILITIES = {
        "query": True,
        "get_key": True,
        "delete_key": True,
        "flush_cache": True,
    }

    def _get_redis_connection(self):
        """
        Get the underlying Redis connection.

        Handles both Django's built-in RedisCache and django-redis.
        """
        # Try django-redis first (most common)
        if hasattr(self.cache, "client"):
            # django-redis
            return self.cache.client.get_client()
        elif hasattr(self.cache, "_cache"):
            # Django's built-in RedisCache
            return self.cache._cache
        else:
            raise AttributeError("Cannot find Redis connection in cache object")

    def _scan_keys(
        self,
        pattern: str = "*",
        page: int = 1,
        per_page: int = 25,
        scan_count: int = 100,
    ):
        """
        Scan Redis for keys matching the pattern using the SCAN command.

        SCAN is cursor-based and doesn't block the server like KEYS does.
        """
        connection = self._get_redis_connection()

        # Convert our pattern to Redis pattern if needed
        # If no wildcards, treat as exact match with wildcards
        if pattern and pattern != "*":
            redis_pattern = pattern
        else:
            redis_pattern = "*"

        # For django-redis, we need to add the cache's key prefix
        if hasattr(self.cache, "make_key"):
            # Get the prefix pattern
            prefix_pattern = self.cache.make_key(redis_pattern)
        else:
            prefix_pattern = redis_pattern

        # Use SCAN to get all matching keys
        # SCAN returns an iterator in redis-py
        all_keys = []
        cursor = 0

        try:
            # Use SCAN with pattern matching
            while True:
                cursor, keys = connection.scan(
                    cursor=cursor, match=prefix_pattern, count=scan_count
                )
                all_keys.extend(keys)

                if cursor == 0:
                    break

            # Decode keys if they're bytes
            decoded_keys = []
            for key in all_keys:
                if isinstance(key, bytes):
                    key = key.decode("utf-8")

                # Remove the cache prefix to get the original key
                if hasattr(self.cache, "make_key"):
                    # Try to reverse the make_key transformation
                    # Django/django-redis typically adds prefix like ":1:prefix:key"
                    if hasattr(self.cache, "key_prefix") and self.cache.key_prefix:
                        if key.startswith(self.cache.key_prefix):
                            key = key[len(self.cache.key_prefix) :]

                    # Remove version prefix (format is :VERSION:key)
                    if key.startswith(":"):
                        parts = key.split(":", 2)
                        if len(parts) >= 3:
                            key = parts[2]

                decoded_keys.append(key)

            # Sort for consistent pagination
            decoded_keys.sort()

            # Apply pagination
            total_count = len(decoded_keys)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_keys = decoded_keys[start_idx:end_idx]

            return {
                "keys": paginated_keys,
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
            }
        except Exception as e:
            # If SCAN fails, return empty result
            return {
                "keys": [],
                "total_count": 0,
                "page": page,
                "per_page": per_page,
                "error": str(e),
            }


class RedisClusterCachePanel(CachePanel):
    """
    Implements the cache panel for Redis cluster instances.

    Redis clusters require different handling than standalone instances
    as keys are distributed across multiple nodes.

    Query support is not yet implemented for clusters.
    """

    ABILITIES = {
        "query": False,  # Not yet implemented for clusters
        "get_key": True,
        "delete_key": True,
        "flush_cache": True,
    }
