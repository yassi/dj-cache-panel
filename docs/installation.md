# Installation

This guide will walk you through installing and setting up Django Cache Panel in your Django project.

## Prerequisites

Before installing Django Cache Panel, make sure you have:

- Python 3.9 or higher
- Django 4.2 or higher
- A configured `CACHES` setting in your Django project

## Installation Steps

### 1. Install the Package

Install Django Cache Panel using pip:

```bash
pip install dj-cache-panel
```

### 2. Add to Django Settings

Add `dj_cache_panel` to your `INSTALLED_APPS` in your Django settings file:

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dj_cache_panel',  # Add this line
    # ... your other apps
]
```

!!! note
    Django Cache Panel doesn't require any database migrations as it doesn't define any Django models.

### 3. Configure Cache Backends

Django Cache Panel uses your existing `CACHES` setting. Make sure you have at least one cache backend configured:

```python
# settings.py
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

### 4. Include URLs

Add the Django Cache Panel URLs to your main `urls.py` file:

```python
# urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/cache/', include('dj_cache_panel.urls')),  # Add this line
    path('admin/', admin.site.urls),
]
```

!!! tip
    You can change the URL path from `admin/cache/` to any path you prefer.

### 5. Create Admin User (if needed)

If you don't already have a Django admin superuser, create one:

```bash
python manage.py createsuperuser
```

### 6. Start the Development Server

Start your Django development server:

```bash
python manage.py runserver
```

### 7. Access the Panel

1. Navigate to the Django admin at `http://127.0.0.1:8000/admin/`
2. Log in with your admin credentials
3. Look for the **"DJ_CACHE_PANEL"** section in the admin interface
4. Click **"Manage Cache keys and values"** to view your cache configuration

## Verification

To verify that everything is working correctly:

1. Check that you can see the Cache Panel section in your Django admin
2. Click on "Manage Cache keys and values"
3. You should see a list of your configured cache backends from the `CACHES` setting

## Troubleshooting

### Common Issues

**Permission denied**
: Ensure you're logged in as a staff user with admin access.

**Module not found**
: Make sure `dj_cache_panel` is properly installed and added to `INSTALLED_APPS`.

**URLs not found**
: Verify that you've included the Cache Panel URLs in your main `urls.py` file.

**No caches visible**
: Ensure you have a `CACHES` setting configured in your Django settings file.

### Getting Help

If you encounter any issues during installation:

- Check the [Quick Start](quick-start.md) guide
- [Open an issue on GitHub](https://github.com/yassi/dj-cache-panel/issues)

## Next Steps

Now that you have Django Cache Panel installed:

- [Follow the quick start guide](quick-start.md)
- [Explore features](features.md)
