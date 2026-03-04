# Testing

Comprehensive test suite for Django Cache Panel.

## Overview

Tests are functional (end-to-end) and target the view layer to ensure complete coverage.

## Test Structure

```
tests/
├── base.py              # Base test class and configuration
├── conftest.py          # Pytest configuration
├── test_admin.py        # Admin integration tests
├── test_key_search.py   # Key search functionality
├── test_add_key.py      # Adding keys
├── test_edit_key.py     # Editing keys
├── test_delete_key.py   # Deleting keys
└── test_flush_cache.py  # Flushing caches
```

## Running Tests

### Prerequisites

Redis, Valkey, and Memcached must be running:

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or start individual containers
docker run -d -p 6379:6379 redis:latest
docker run -d -p 6380:6380 valkey/valkey:latest
docker run -d -p 11211:11211 memcached:latest
docker run -d -p 5432:5432 postgres:latest
```

### Run All Tests

```bash
# Using Make with Docker
make test_docker

# Using Make locally
make test_local

# Using pytest directly
pytest tests/

# With verbose output
pytest tests/ -v
```

### Testing with Valkey Support

Django Cache Panel includes comprehensive testing for the optional Valkey backend:

```bash
# Test with Valkey support enabled (Docker)
INSTALL_VALKEY=true make test_docker

# Test locally with Valkey
INSTALL_VALKEY=true make test_local

# Test with specific Python version
PYTHON_VERSION=3.11 INSTALL_VALKEY=true make test_docker
```

**Note:** When `INSTALL_VALKEY=false`:
- `django_valkey` is not installed
- Tests automatically skip Valkey backend
- All other cache backends are tested normally

### Run Specific Tests

```bash
# Single file
pytest tests/test_add_key.py

# Single test
pytest tests/test_add_key.py::TestAddKey::test_add_simple_string_key

# With pattern
pytest tests/ -k "add_key"
```

### With Coverage

```bash
pytest --cov=dj_cache_panel tests/

# HTML report
pytest --cov=dj_cache_panel --cov-report=html tests/
open htmlcov/index.html
```

## Test Configuration

### Cache Backends (`base.py`)

Tests run against multiple backends:

```python
TEST_CACHES = {
    'default': LocMemCache,
    'locmem': LocMemCache,
    'database': DatabaseCache,
    'filesystem': FileBasedCache,
    'dummy': DummyCache,
    'redis': RedisCache,
    'django_redis': DjangoRedisCache,
    'django_valkey': DjangoValkeyCache,
    'memcached': MemcachedCache,
}
```

### Cache Categories

Tests iterate through categorized caches:

- **QUERY_SUPPORTED_CACHES**: `locmem`, `database`, `redis`, `django_redis`, `django_valkey` (if installed)
- **NON_QUERY_CACHES**: `dummy`, `filesystem`, `memcached`
- **OPERATIONAL_CACHES**: `locmem`, `redis`, `django_redis`, `django_valkey` (if installed), `memcached`, `database`

### Valkey Backend Support

The `django_valkey` cache backend is included in test coverage when:
1. `django-valkey` package is installed
2. Valkey service is running on port 6380

The test suite automatically detects whether Valkey is available and includes/excludes it from test runs accordingly using `importlib.util.find_spec()` for safe runtime detection.

Test configuration in `tests/base.py`:
```python
if importlib.util.find_spec("django_valkey") is not None:
    QUERY_SUPPORTED_CACHES.append("django_valkey")
    OPERATIONAL_CACHES.append("django_valkey")
    TEST_CACHES["django_valkey"] = {
        "BACKEND": "django_valkey.cache.ValkeyCache",
        "LOCATION": f"valkey://{VALKEY_HOST}:{VALKEY_PORT}/2",
    }
```
- **OPERATIONAL_CACHES**: All except `dummy`

## Test Patterns

### View Layer Testing

Tests go through Django views (not direct panel access):

```python
def test_add_key(self):
    for cache_name in OPERATIONAL_CACHES:
        with self.subTest(cache=cache_name):
            cache = caches[cache_name]
            
            # Test via view
            url = reverse("dj_cache_panel:key_add", args=[cache_name])
            response = self.client.post(url, {"key": "test", "value": "val"})
            
            # Verify in cache
            self.assertEqual(cache.get("test"), "val")
```

### SubTests for Multiple Backends

Each test runs against relevant backends:

```python
def test_feature(self):
    for cache_name in QUERY_SUPPORTED_CACHES:
        with self.subTest(cache=cache_name):
            # Test implementation
            pass
```

## Test Coverage

### Admin Integration (`test_admin.py`)

- Panel appears in admin
- Redirects work correctly
- Authentication required
- Staff-only access

### Key Search (`test_key_search.py`)

- Page loads for all backends
- Wildcard search works
- Exact key lookup
- Pagination
- Empty results
- Backend-specific messages

### Add Keys (`test_add_key.py`)

- Simple string values
- JSON values
- Custom timeouts
- Success messages
- Duplicate key handling
- Authentication required

### Edit Keys (`test_edit_key.py`)

- Update string values
- Update JSON values
- Custom timeouts
- Success messages
- Non-existent key handling
- Special characters in keys

### Delete Keys (`test_delete_key.py`)

- Delete existing keys
- Success messages
- Non-existent key handling
- Multiple deletions
- Special characters in keys

### Flush Cache (`test_flush_cache.py`)

- Removes all keys
- Success messages
- Disabled cache handling
- Authentication required

## Environment Variables

Configure external services:

```bash
# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379

# Memcached
export MEMCACHED_HOST=localhost
export MEMCACHED_PORT=11211
```

## CI/CD Integration

### GitHub Actions

```yaml
services:
  redis:
    image: redis:latest
    ports:
      - 6379:6379
  valkey:
    image: valkey/valkey:latest
    ports:
      - 6380:6380
  memcached:
    image: memcached:latest
    ports:
      - 11211:11211

env:
  REDIS_HOST: localhost
  VALKEY_HOST: localhost
  MEMCACHED_HOST: localhost
```

### GitLab CI

```yaml
services:
  - redis:latest
  - valkey:latest
  - memcached:latest

variables:
  REDIS_HOST: redis
  VALKEY_HOST: rvalkeys
  MEMCACHED_HOST: memcached
```

## Writing Tests

### Test Template

```python
from .base import CacheTestCase, OPERATIONAL_CACHES
from django.urls import reverse
from django.core.cache import caches

class TestMyFeature(CacheTestCase):
    def test_my_feature(self):
        for cache_name in OPERATIONAL_CACHES:
            with self.subTest(cache=cache_name):
                cache = caches[cache_name]
                
                # Setup
                cache.set("test_key", "test_value", timeout=300)
                
                # Execute
                url = reverse("dj_cache_panel:view_name", args=[cache_name])
                response = self.client.get(url)
                
                # Assert
                self.assertEqual(response.status_code, 200)
```

### Guidelines

1. **Test through views**: Don't access panel classes directly
2. **Use subTest**: Run against multiple backends
3. **Clean up**: `setUp` and `tearDown` handle cache clearing
4. **Be specific**: Use appropriate cache categories
5. **Check both**: Response status AND cache state

## Debugging Tests

### Run with verbose output

```bash
pytest tests/ -vv
```

### Run with print statements

```bash
pytest tests/ -s
```

### Run single test with debugger

```bash
pytest tests/test_add_key.py::TestAddKey::test_add_simple_string_key --pdb
```

### Check specific cache

```bash
# Test only LocMem
pytest tests/ -k "locmem"

# Test only Redis
pytest tests/ -k "redis"
```

## Common Issues

### Redis or Valkey Connection Refused

**Error**: `redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`

**Solution**: Start Redis:
```bash
docker run -d -p 6379:6379 redis:latest
```

**Solution**: Start Valkey:
```bash
docker run -d -p 6380:6380 valkey/valkey:latest
```


### Memcached Connection Issues

**Error**: Connection errors to Memcached

**Solution**: Start Memcached:
```bash
docker run -d -p 11211:11211 memcached:latest
```

### Database Locked

**Error**: `database is locked`

**Solution**: Using SQLite in tests is fine, but avoid parallel execution:
```bash
pytest tests/ -n0  # Disable parallel
```
