# Django Cache Panel

A universal cache inspector for Django.

## Overview

Django Cache Panel is a Django admin extension that provides a web interface for inspecting and managing your Django cache backends. It works with any cache backend configured in your Django `CACHES` setting.

## Key Features

- **Browse Cache Instances**: View all configured cache backends
- **Abilities Matrix**: See which operations each cache supports
- **Key Management**: Search, view, edit, delete, and add cache keys
- **Backend Agnostic**: Works with LocMem, Database, Redis, Memcached, File-based, and more
- **Admin Integration**: Seamlessly integrates with Django's admin interface
- **Secure**: Only accessible to staff users

## Supported Backends

All Django cache backends are supported with varying levels of functionality:

| Backend | Query | Get | Edit | Add | Delete | Flush |
|---------|-------|-----|------|-----|--------|-------|
| LocMemCache | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| DatabaseCache | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| RedisCache (Django) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| RedisCache (django-redis) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FileBasedCache | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| MemcachedCache | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| DummyCache | — | — | — | — | — | — |

**Query**: List/search keys with patterns  
**Get**: Retrieve individual keys by name  
**Edit**: Modify existing key values  
**Add**: Create new cache entries  
**Delete**: Remove keys from cache  
**Flush**: Clear all cache entries


Note: Even if the a functionality appears not available in the matrix above, `dj-cache-panel` allows custom
defined classes that can customize logic for these abilities.
## Quick Links

- [Installation](installation.md)
- [Configuration](configuration.md)
- [Features](features.md)
- [Development](development.md)
- [Testing](testing.md)

## Requirements

- Python 3.9+
- Django 4.2+

## License

MIT License - See [LICENSE](https://github.com/yassi/dj-cache-panel/blob/main/LICENSE) file for details.
