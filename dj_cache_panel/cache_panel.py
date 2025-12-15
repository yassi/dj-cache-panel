import fnmatch
import time
from django.db import connection
from django.conf import settings
from django.core.cache import caches


DJ_CACHE_PANEL_SETTINGS = getattr(settings, "DJ_CACHE_PANEL_SETTINGS", {})


# Default Mapping of backend class paths to panel classes
BACKEND_PANEL_MAP_DEFAULT = {
    # Local memory cache
    "django.core.cache.backends.locmem.LocMemCache": "LocalMemoryCachePanel",
    # Redis backends (standalone - cluster detection happens in get_cache_panel)
    "django.core.cache.backends.redis.RedisCache": "RedisCachePanel",  # Django's built-in (4.0+)
    "django_redis.cache.RedisCache": "DjangoRedisCachePanel",  # django-redis library
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

# Replace the default backend panel map with any custom mappings. Should realistically never be used.
BACKEND_PANEL_MAP = DJ_CACHE_PANEL_SETTINGS.get(
    "BACKEND_PANEL_MAP", BACKEND_PANEL_MAP_DEFAULT
)

BACKEND_PANEL_EXTENSIONS = DJ_CACHE_PANEL_SETTINGS.get("BACKEND_PANEL_EXTENSIONS", {})
# Merge the default backend panel map with any custom extensions.
BACKEND_PANEL_MAP.update(BACKEND_PANEL_EXTENSIONS)

CACHES_SETTINGS = DJ_CACHE_PANEL_SETTINGS.get("CACHES", {})


def get_cache_panel(cache_name: str):
    """
    Returns the proper CachePanel subclass for the given cache name. This function
    inspects the cache configuration and returns the appropriate subclass.

    The panel class can be specified as:
    - A simple class name (e.g., "RedisCachePanel") - looked up in this module
    - A full module path (e.g., "myapp.panels.CustomCachePanel") - imported dynamically
    """
    cache_config = settings.CACHES.get(cache_name)
    if not cache_config:
        raise ValueError(f"Cache '{cache_name}' is not configured in CACHES setting.")

    backend = cache_config.get("BACKEND", "")

    panel_class_name = BACKEND_PANEL_MAP.get(backend)
    if panel_class_name:
        # Check if this is a full module path (contains a dot)
        if "." in panel_class_name:
            # Dynamic import from module path
            try:
                module_path, class_name = panel_class_name.rsplit(".", 1)
                from importlib import import_module

                module = import_module(module_path)
                panel_class = getattr(module, class_name, None)
                if panel_class:
                    return panel_class(cache_name)
                else:
                    raise AttributeError(
                        f"Class '{class_name}' not found in module '{module_path}'"
                    )
            except (ImportError, AttributeError, ValueError) as e:
                raise ImportError(
                    f"Failed to import panel class '{panel_class_name}': {str(e)}"
                )
        else:
            # Simple class name - get from this module's globals
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
        "edit_key": False,
        "add_key": False,
        "flush_cache": False,
    }

    def __init__(self, cache_name: str):
        self.cache_name = cache_name
        self.cache_settings = CACHES_SETTINGS.get(self.cache_name, {})

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
        override_abilities = self.cache_settings.get("abilities", {})
        computed_abilities = {}
        for feature, value in self.ABILITIES.items():
            computed_abilities[feature] = value
            if feature in override_abilities:
                computed_abilities[feature] = override_abilities[feature]
        return computed_abilities

    def is_feature_supported(self, feature: str):
        """
        Returns True if the cache panel supports the given feature.
        """
        return self.abilities.get(feature, False)

    def _query(
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
        return self._query(pattern, page, per_page, scan_count)

    def _get_key(self, key: str):
        """
        Get a key value from the database cache.

        Django's cache.get() handles the key transformation automatically,
        so we can use it directly.

        Override this method to implement custom get logic.
        """
        # Use sentinel to check if key exists (handles None values)
        sentinel = object()
        value = self.cache.get(key, sentinel)
        exists = value is not sentinel

        # If key doesn't exist, value should be None for the return
        if not exists:
            value = None

        return {
            "key": key,
            "value": value,
            "exists": exists,
            "type": type(value).__name__ if value is not None else None,
            "expiry": None,  # TTL not available via Django's cache framework
        }

    def get_key(self, key: str):
        """
        Get a key value from the cache.

        standard gating provided in this class to prevent accidental misuse.
        """
        if not self.is_feature_supported("get_key"):
            raise NotImplementedError(
                "Getting keys is not supported for this cache backend."
            )
        return self._get_key(key)

    def _delete_key(self, key: str):
        """
        Delete a key from the cache.

        Override this method to implement custom delete logic.
        """
        self.cache.delete(key)
        return {
            "success": True,
            "error": None,
            "message": f"Key {key} deleted successfully.",
        }

    def delete_key(self, key: str):
        """
        Delete a key from the cache.

        standard gating provided in this class to prevent accidental misuse.
        """
        if not self.is_feature_supported("delete_key"):
            raise NotImplementedError(
                "Deleting keys is not supported for this cache backend."
            )
        return self._delete_key(key)

    def _edit_key(self, key: str, value, timeout=None):
        """
        Update the value of a cache key.

        Override this method to implement custom edit logic.

        Args:
            key: The cache key to update
            value: The new value for the key
            timeout: Optional timeout in seconds. If None, uses cache default or preserves existing TTL.
        """
        # Use set with timeout if provided, otherwise preserve existing TTL if possible
        # Django's cache.set() will update the value
        self.cache.set(key, value, timeout=timeout)
        return {
            "success": True,
            "error": None,
            "message": f"Key {key} updated successfully.",
        }

    def edit_key(self, key: str, value, timeout=None):
        """
        Update the value of a cache key.

        standard gating provided in this class to prevent accidental misuse.

        Args:
            key: The cache key to update
            value: The new value for the key
            timeout: Optional timeout in seconds. If None, uses cache default or preserves existing TTL.
        """
        if not self.is_feature_supported("edit_key"):
            raise NotImplementedError(
                "Editing keys is not supported for this cache backend."
            )
        return self._edit_key(key, value, timeout=timeout)

    def _flush_cache(self):
        """
        Clear all entries from the cache.

        Override this method to implement custom flush logic.
        """
        self.cache.clear()
        return {
            "success": True,
            "error": None,
            "message": "Cache flushed successfully.",
        }

    def flush_cache(self):
        """
        Clear all entries from the cache.

        standard gating provided in this class to prevent accidental misuse.
        """
        if not self.is_feature_supported("flush_cache"):
            raise NotImplementedError(
                "Flushing the cache is not supported for this cache backend."
            )
        return self._flush_cache()


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
        "edit_key": True,
        "add_key": True,
        "flush_cache": True,
    }

    def _get_internal_cache(self):
        """
        Access the internal cache dictionary of LocMemCache.
        The LocMemCache uses self._cache as the storage dict.
        """
        return getattr(self.cache, "_cache", {})

    def _query(
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
        "edit_key": True,
        "add_key": True,
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

    def _query(
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
        # quoted table - different databases have different quoting conventions
        quoted_table_name = connection.ops.quote_name(table_name)

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
        # The database cache backend stores expires differently by database:
        # - SQLite: decimal/float timestamp (numeric)
        # - PostgreSQL: timestamp with time zone
        # - MySQL: can vary based on Django version and configuration
        # - Oracle: timestamp
        # We need to handle both cases
        current_time = time.time()

        # Query for keys that match the pattern and haven't expired
        with connection.cursor() as cursor:
            if connection.vendor in ("postgresql", "oracle"):
                expires_condition = "expires > to_timestamp(%s)"
            elif connection.vendor == "mysql":
                expires_condition = "expires > FROM_UNIXTIME(%s)"
            else:
                # SQLite and others store as numeric
                expires_condition = "expires > %s"

            # Count total matching keys that haven't expired
            count_sql = f"""
                SELECT COUNT(*) 
                FROM {quoted_table_name} 
                WHERE cache_key LIKE %s AND {expires_condition}
            """
            cursor.execute(count_sql, [sql_pattern, current_time])
            total_count = cursor.fetchone()[0]

            # Get paginated keys
            start_idx = (page - 1) * per_page
            keys_sql = f"""
                SELECT cache_key 
                FROM {quoted_table_name}
                WHERE cache_key LIKE %s AND {expires_condition}
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
        "edit_key": True,
        "add_key": True,
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
        "edit_key": False,
        "add_key": False,
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
        "edit_key": False,  # Dummy cache doesn't actually store values
        "add_key": False,
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
        "edit_key": True,
        "add_key": True,
        "flush_cache": True,
    }


class DjangoRedisCachePanel(CachePanel):
    """
    Implements the cache panel for standalone Redis instances.

    Uses the SCAN command to iterate through keys efficiently without
    blocking the Redis server.
    """

    ABILITIES = {
        "query": True,
        "get_key": True,
        "delete_key": True,
        "edit_key": True,
        "add_key": True,
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

    def _query(
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

            # Decode keys if they're bytes and store both prefixed and original keys
            decoded_keys = []
            for prefixed_key in all_keys:
                if isinstance(prefixed_key, bytes):
                    prefixed_key = prefixed_key.decode("utf-8")

                # Store the original prefixed key
                original_prefixed_key = prefixed_key

                # Remove the cache prefix to get the original key
                user_key = prefixed_key
                if hasattr(self.cache, "make_key"):
                    # Try to reverse the make_key transformation
                    # Django/django-redis typically adds prefix like ":1:prefix:key"
                    if hasattr(self.cache, "key_prefix") and self.cache.key_prefix:
                        if prefixed_key.startswith(self.cache.key_prefix):
                            user_key = prefixed_key[len(self.cache.key_prefix) :]

                    # Remove version prefix (format is :VERSION:key)
                    if user_key.startswith(":"):
                        parts = user_key.split(":", 2)
                        if len(parts) >= 3:
                            user_key = parts[2]

                decoded_keys.append(
                    {
                        "key": user_key,
                        "redis_key": original_prefixed_key,
                    }
                )

            # Sort for consistent pagination (by user key)
            decoded_keys.sort(key=lambda x: x["key"])

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


class RedisCachePanel(CachePanel):
    """
    Implements the cache panel for Django's built-in RedisCache backend.

    This is specifically for django.core.cache.backends.redis.RedisCache
    introduced in Django 4.0+.

    Django's built-in backend uses a simpler key format than django-redis:
    - Keys are stored as ":VERSION:key" (no key_prefix support in the same way)
    """

    ABILITIES = {
        "query": True,
        "get_key": True,
        "delete_key": True,
        "edit_key": True,
        "add_key": True,
        "flush_cache": True,
    }

    def _get_redis_connection(self):
        """
        Get the underlying Redis connection for Django's built-in RedisCache.

        Django's RedisCache stores a RedisCacheClient wrapper in _cache attribute.
        The RedisCacheClient has a get_client() method that returns the actual Redis client.
        """
        if hasattr(self.cache, "_cache"):
            cache_client = self.cache._cache
            # The RedisCacheClient has a get_client() method
            if hasattr(cache_client, "get_client"):
                # get_client() returns the actual redis.Redis instance
                return cache_client.get_client()
            elif hasattr(cache_client, "_client"):
                # Some versions might store it directly
                client = cache_client._client
                # Check if _client is a callable or class that needs instantiation
                if callable(client) and not hasattr(client, "scan"):
                    # It might be a class, try calling it
                    return client()
                return client
            else:
                # Try returning the cache_client itself as a fallback
                return cache_client
        else:
            raise AttributeError("Cannot find Redis connection in Django RedisCache")

    def _query(
        self,
        pattern: str = "*",
        page: int = 1,
        per_page: int = 25,
        scan_count: int = 100,
    ):
        """
        Scan Redis for keys matching the pattern using the SCAN command.

        Django's built-in RedisCache uses format: ":VERSION:key"
        """
        try:
            connection = self._get_redis_connection()
        except Exception as e:
            return {
                "keys": [],
                "total_count": 0,
                "page": page,
                "per_page": per_page,
                "error": f"Failed to get Redis connection: {str(e)}",
            }

        # Scan all keys - Django's built-in backend stores keys as ":VERSION:key"
        redis_pattern = "*"

        # Use SCAN to get all matching keys
        all_keys = []
        cursor = 0

        try:
            # Use SCAN with pattern matching
            while True:
                cursor, keys = connection.scan(
                    cursor=cursor, match=redis_pattern, count=scan_count
                )
                all_keys.extend(keys)

                if cursor == 0:
                    break

            # Decode keys if they're bytes and transform back to user-facing keys
            decoded_keys = []
            for prefixed_key in all_keys:
                if isinstance(prefixed_key, bytes):
                    prefixed_key = prefixed_key.decode("utf-8")

                # Store the original prefixed key
                original_prefixed_key = prefixed_key

                # Remove the version prefix to get the original key
                # Django's format is ":VERSION:key"
                user_key = prefixed_key
                if prefixed_key.startswith(":"):
                    parts = prefixed_key.split(":", 2)
                    if len(parts) >= 3:
                        user_key = parts[2]
                    elif len(parts) == 2:
                        user_key = parts[1]

                # Apply pattern matching if provided
                if pattern and pattern != "*":
                    if "*" in pattern or "?" in pattern:
                        # Wildcard pattern - use fnmatch
                        if not fnmatch.fnmatch(user_key, pattern):
                            continue
                    else:
                        # Exact match
                        if user_key != pattern:
                            continue

                decoded_keys.append(
                    {
                        "key": user_key,
                        "redis_key": original_prefixed_key,
                    }
                )

            # Sort for consistent pagination (by user key)
            decoded_keys.sort(key=lambda x: x["key"])

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
            # If SCAN fails, return empty result with error
            import traceback

            return {
                "keys": [],
                "total_count": 0,
                "page": page,
                "per_page": per_page,
                "error": f"SCAN failed: {str(e)}\n{traceback.format_exc()}",
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
        "edit_key": True,
        "add_key": True,
        "flush_cache": True,
    }
