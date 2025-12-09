# Features

This page describes the features available in Django Cache Panel.

## Django Admin Integration

Django Cache Panel integrates seamlessly into your existing Django admin interface. A new section for cache management appears alongside your regular Django models.

!!! note "No Models Required"
    This application doesn't introduce any Django models or require database migrations. It's purely a cache configuration viewing interface.

![Admin Home](https://raw.githubusercontent.com/yassi/dj-redis-panel/main/images/admin_home.png)

**Features shown:**
- Clean integration with Django admin styling
- Cache Panel section in the admin home
- "Manage Cache keys and values" entry point

## Cache Configuration View

The main page shows all configured cache backends from your `CACHES` setting.

**Features:**
- List of all cache backends
- Cache name and backend class display
- Clean, organized table format

## Permission Control

Django Cache Panel respects Django's built-in permission system:

- **Staff users only**: Only users with `is_staff=True` can access the panel
- **Admin integration**: Uses Django admin's authentication and authorization
- **No additional permissions**: Works with your existing admin setup

## Multiple Cache Backends

The panel displays all cache backends defined in your `CACHES` setting:

- **Default cache**: Usually named "default"
- **Named caches**: Any additional cache configurations
- **Different backends**: Supports all Django cache backends (Redis, Memcached, LocMem, etc.)

## Getting the Most from the Interface

### Best Practices

1. **Use Descriptive Names**: Name your cache backends clearly (e.g., "session", "api_cache")
2. **Monitor Configuration**: Use the panel to verify your cache configuration is correct
3. **Development Tool**: Great for quickly checking cache setup during development

## Future Features

Django Cache Panel is actively developed. Planned features include:

- Key browsing and inspection
- Cache statistics and metrics
- Key management operations

The interface continues to evolve with new features and improvements in each release.
