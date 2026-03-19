# Development

Contributing to Django Cache Panel or setting up for local development.

## Prerequisites

- Python 3.9-3.14
- Git
- Docker (recommended)
- Redis, Valkey & Memcached (for testing)

## Setup

### 1. Clone Repository

```bash
git clone https://github.com/yassi/dj-cache-panel.git
cd dj-cache-panel
```

### 2. Choose Development Environment

#### Option A: Docker (Recommended)

```bash
make docker_up       # Start all services
make docker_shell    # Open shell in container
```

**With Valkey Support:**
```bash
INSTALL_VALKEY=true make docker_up
INSTALL_VALKEY=true make docker_shell
```

**With Different Python Version:**
```bash
PYTHON_VERSION=3.11 make docker_up
PYTHON_VERSION=3.11 INSTALL_VALKEY=true make docker_up
```

Services included:
- Redis (port 6379)
- Valkey (port 6380)
- Memcached (port 11211)
- PostgreSQL (port 5432)
- Development container

#### Option B: Local Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install package and dependencies
make install

# Or with Valkey support
INSTALL_VALKEY=true make install
```

Alternative manual installation:
```bash
pip install -e .
pip install -r requirements.txt

# For Valkey support
pip install -e .[dev,valkey]
```

Start external services:
```bash
# Redis
docker run -d -p 6379:6379 redis:latest

# Valkey
docker run -d -p 6380:6380 valkey/valkey:latest

# Memcached
docker run -d -p 11211:11211 memcached:latest
```

### 3. Set Up Example Project

```bash
cd example_project
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/admin/`

## Testing

### Run All Tests

```bash
# Docker
make test_docker

# Local
make test_local
```

### Testing with Valkey Support

```bash
# Docker with Valkey
INSTALL_VALKEY=true make test_docker

# Local (requires Valkey installed: pip install django-valkey)
INSTALL_VALKEY=true make test_local
```

### Testing with Different Python Versions

```bash
# Docker with Python 3.11
PYTHON_VERSION=3.11 make test_docker

# Docker with Python 3.11 and Valkey
PYTHON_VERSION=3.11 INSTALL_VALKEY=true make test_docker
```

**Note:** Valkey support is optional and depends on `django-valkey`. If it's not installed, Valkey tests are automatically skipped.

### Run Specific Tests

```bash
pytest tests/test_key_search.py -v
pytest tests/test_add_key.py::TestAddKey::test_add_simple_string_key
```

### With Coverage

```bash
pytest --cov=dj_cache_panel tests/
```

## Project Structure

```
dj-cache-panel/
├── dj_cache_panel/           # Main package
│   ├── cache_panel.py        # Backend-specific panel classes
│   ├── views.py              # Django views
│   ├── urls.py               # URL patterns
│   ├── models.py             # Placeholder model
│   ├── admin.py              # Admin integration
│   └── templates/            # HTML templates
├── tests/                    # Test suite
│   ├── base.py               # Test base class
│   ├── test_*.py             # Test modules
│   └── conftest.py           # Pytest configuration
├── example_project/          # Example Django project
├── docs/                     # Documentation
└── Makefile                  # Development commands
```

## Key Components

### Panel Classes (`cache_panel.py`)

Base class for cache backend implementations:

```python
class CachePanel:
    ABILITIES = {
        "query": False,
        "get_key": False,
        # ...
    }
    
    def _query(self, pattern, page, per_page):
        """Implement key listing"""
        pass
```

Subclass for specific backends:
- `LocalMemoryCachePanel`
- `DatabaseCachePanel`
- `RedisCachePanel`
- `DjangoRedisCachePanel`
- `ValkeyCachePanel`
- `FileBasedCachePanel`
- `MemcachedCachePanel`
- `DummyCachePanel`

### Views (`views.py`)

- `index`: List all caches
- `key_search`: Search and browse keys
- `key_detail`: View/edit/delete individual key
- `key_add`: Add new keys

### Tests (`tests/`)

View-layer functional tests:
- Test through Django test client
- Run against all cache backends
- Use `subTest` for backend iteration

## Environment Variables Reference

When developing or testing, you can use these environment variables to control the build and installation:

### Installation & Setup

| Variable | Default | Description |
|----------|---------|-------------|
| `INSTALL_VALKEY` | `false` | Install `django-valkey` optional dependency |
| `PYTHON_VERSION` | `3.10` | Python version to use in Docker containers |

### Examples

```bash
# Default: Python 3.10, no Valkey
make install
make test_docker

# With Valkey support (local)
INSTALL_VALKEY=true make install

# Different Python version (Docker)
PYTHON_VERSION=3.11 make docker_up

# All options combined
PYTHON_VERSION=3.12 INSTALL_VALKEY=true make test_docker
```

## Making Changes

### Adding a New Feature

1. Update panel class if needed
2. Modify view logic
3. Update template
4. Add tests
5. Update documentation

### Adding Backend Support

1. Create new panel class in `cache_panel.py`
2. Define `ABILITIES`
3. Implement `_query` (if supported)
4. Add to `BACKEND_PANEL_MAP_DEFAULT`
5. Add tests

### Modifying Templates

Templates use Django admin styling:
- Extend `admin/dj_cache_panel/base.html`
- Use admin CSS variables
- Support dark mode

## Code Style

- Follow PEP 8
- Use type hints where helpful
- Write docstrings for public methods
- Keep functions focused and small

## Running Linters

```bash
# Linters run automatically with read_lints tool
# Or run manually:
ruff check dj_cache_panel/
```

## Makefile Commands

```bash
make install        # Install dependencies
make test_local     # Run tests locally
make test_docker    # Run tests in Docker
make docker_up      # Start Docker services
make docker_down    # Stop Docker services
make docker_shell   # Open shell in container
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run test suite
6. Submit pull request

## Environment Variables

For testing with Docker:

```bash
REDIS_HOST=redis        # Default: localhost
REDIS_PORT=6379         # Default: 6379
VALKEY_HOST=valkey        # Default: localhost
VALKEY_PORT=6380         # Default: 6380
MEMCACHED_HOST=memcached # Default: localhost
MEMCACHED_PORT=11211    # Default: 11211
```
