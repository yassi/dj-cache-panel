# Configuration

Django Cache Panel works out of the box with your existing Django `CACHES` configuration. Advanced configuration is optional.

## Basic Configuration

The only required configuration is your Django `CACHES` setting:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'redis': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    },
}
```

## Advanced Configuration

For advanced use cases, you can customize behavior with `DJ_CACHE_PANEL_SETTINGS`:

```python
DJ_CACHE_PANEL_SETTINGS = {
    # Custom panel mappings
    "BACKEND_PANEL_EXTENSIONS": {},
    
    # Per-cache ability overrides
    "CACHES": {},
}
```

### Custom Panel Mappings

Map custom cache backends to panel classes:

```python
DJ_CACHE_PANEL_SETTINGS = {
    "BACKEND_PANEL_EXTENSIONS": {
        # Map custom backend to custom panel
        "myapp.backends.CustomCache": "myapp.panels.CustomCachePanel",
        
        # Override built-in backend
        "django.core.cache.backends.redis.RedisCache": "myapp.panels.MyRedisPanel",
    },
}
```

Panel classes can be specified as:

- **Simple name**: `"RedisCachePanel"` (looked up in `dj_cache_panel.cache_panel`)
- **Full path**: `"myapp.panels.CustomCachePanel"` (imported dynamically)

### Per-Cache Ability Overrides

Restrict operations for specific caches:

```python
DJ_CACHE_PANEL_SETTINGS = {
    "CACHES": {
        "production_cache": {
            "abilities": {
                "query": True,
                "get_key": True,
                "delete_key": False,  # Disable deletes
                "edit_key": False,    # Disable edits
                "add_key": False,     # Disable adds
                "flush_cache": False, # Disable flush
            },
        },
    },
}
```

Available abilities:

- `query`: List/search keys with patterns
- `get_key`: View individual key values
- `delete_key`: Delete keys
- `edit_key`: Modify key values
- `add_key`: Create new keys
- `flush_cache`: Clear all cache entries

## URLs Configuration

By default, the panel is accessible at `/admin/dj-cache-panel/`. You can change this:

```python
# urls.py
urlpatterns = [
    path('admin/cache/', include('dj_cache_panel.urls')),  # Custom path
    path('admin/', admin.site.urls),
]
```

## Security

Django Cache Panel uses Django's built-in admin authentication:

- Only staff users (`is_staff=True`) can access the panel
- All views require authentication via `@staff_member_required`
- No additional security configuration needed

To restrict access further, use per-cache ability overrides or implement custom panel classes.
