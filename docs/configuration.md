# Configuration

Django Cache Panel uses your existing Django `CACHES` setting. No additional configuration is required.

## Using Django CACHES Setting

Django Cache Panel automatically reads from your `CACHES` setting in `settings.py`:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

The panel will automatically display all cache backends defined in this setting.

## Supported Cache Backends

Django Cache Panel works with any Django cache backend, including:

- **Redis**: `django.core.cache.backends.redis.RedisCache`
- **Memcached**: `django.core.cache.backends.memcached.PyMemcacheCache`
- **Local Memory**: `django.core.cache.backends.locmem.LocMemCache`
- **Database**: `django.core.cache.backends.db.DatabaseCache`
- **File-based**: `django.core.cache.backends.filebased.FileBasedCache`
- **Dummy**: `django.core.cache.backends.dummy.DummyCache`
- **Custom backends**: Any custom cache backend class

## Multiple Cache Backends

You can configure multiple cache backends:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    },
    'session': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'api': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
    }
}
```

All configured caches will appear in the panel.

## Environment-Specific Configuration

You can use different cache configurations based on your environment:

```python
# settings.py
import os

if os.getenv('DJANGO_ENV') == 'production':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.getenv('REDIS_URL'),
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
```

The panel will show the appropriate configuration for your current environment.

## Next Steps

- [Quick Start Guide](quick-start.md) - Get started with your configured caches
- [Features Overview](features.md) - Learn about all available features
- [Development Setup](development.md) - Set up for local development
