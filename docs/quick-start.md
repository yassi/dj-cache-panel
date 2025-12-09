# Quick Start Guide

This guide will get you up and running with Django Cache Panel in just a few minutes.

## Prerequisites

Before starting, make sure you have:

- ✅ Django Cache Panel [installed](installation.md)
- ✅ A configured `CACHES` setting in your Django project
- ✅ Django admin access

## Step 1: Access the Admin Panel

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to your Django admin interface:
   ```
   http://127.0.0.1:8000/admin/
   ```

3. Log in with your admin credentials

4. Look for the **"DJ_CACHE_PANEL"** section in the admin home page

## Step 2: View Your Cache Configuration

1. Click on **"Manage Cache keys and values"**

2. You'll see a list of all cache backends defined in your `CACHES` setting:
   - Cache name (e.g., "default", "session")
   - Backend class (e.g., "django.core.cache.backends.redis.RedisCache")

## What You'll See

The cache panel displays:

- **Cache Name**: The key from your `CACHES` dictionary
- **Backend**: The cache backend class being used

This gives you a quick overview of all cache configurations in your Django project.

## Example Configuration

If your `CACHES` setting looks like this:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    },
    'session': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

The panel will show:

| Cache Name | Backend |
|------------|---------|
| default | django.core.cache.backends.redis.RedisCache |
| session | django.core.cache.backends.locmem.LocMemCache |

## Troubleshooting

### Can't see Cache Panel in admin

- Verify `dj_cache_panel` is in `INSTALLED_APPS`
- Check that you're logged in as a staff user
- Ensure URLs are properly configured

### No caches visible

- Verify you have a `CACHES` setting in your Django settings file
- Check that at least one cache backend is configured

## Next Steps

Now that you're familiar with the basics:

- [Explore features](features.md) in detail
- [Set up for development](development.md)
