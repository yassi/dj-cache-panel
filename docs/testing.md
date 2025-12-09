# Testing

Django Cache Panel includes a test suite to ensure reliability and prevent regressions. This guide covers running tests and understanding the testing infrastructure.

## Test Overview

### Test Structure

The test suite is organized in the `tests/` directory:

```
tests/
├── __init__.py
├── base.py                 # Base test classes
├── conftest.py            # Pytest configuration
└── test_admin.py          # Admin integration tests
```

### Test Types

- **Admin Integration Tests**: Tests for Django admin integration and permissions

## Running Tests

### Prerequisites

Before running tests, ensure you have:

- **Development dependencies** installed: `pip install -r requirements.txt`
- **Package installed in editable mode**: `pip install -e .`

### Quick Test Commands

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=dj_cache_panel --cov-report=html

# Run specific test file
pytest tests/test_admin.py -v

# Run tests in parallel
pytest -n auto
```

### Detailed Test Commands

```bash
# Run tests with debugging
pytest --pdb

# Run tests with coverage and HTML report
pytest --cov=dj_cache_panel --cov-report=html

# Run tests with timing information
pytest --durations=10
```

## Test Configuration

### Pytest Configuration

Tests are configured in `pytest.ini`:

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = example_project.settings
testpaths = tests
addopts = --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
```

### Test Settings

Tests use Django's `override_settings` to configure cache backends:

```python
@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
)
class CacheTestCase(TestCase):
    # Test implementation
```

This ensures tests don't require external cache services like Redis.

## Writing Tests

### Test Base Class

All tests inherit from `CacheTestCase` which provides:

- Admin user creation
- Authenticated test client
- Cache configuration via Django settings

```python
from tests.base import CacheTestCase

class TestMyFeature(CacheTestCase):
    def test_something(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
```

### Example Test

```python
from django.urls import reverse
from tests.base import CacheTestCase

class TestCachePanel(CacheTestCase):
    def test_cache_panel_appears_in_admin(self):
        response = self.client.get('/admin/')
        self.assertContains(response, 'dj_cache_panel')
        
        changelist_url = reverse(
            'admin:dj_cache_panel_cachepanelplaceholder_changelist'
        )
        self.assertContains(response, changelist_url)
```

## Test Coverage

The project aims for high test coverage. Run coverage reports to see which areas need more tests:

```bash
pytest --cov=dj_cache_panel --cov-report=term-missing
```

## Continuous Integration

Tests are automatically run in CI/CD pipelines. Make sure all tests pass before submitting pull requests.
