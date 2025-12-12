# Django Cache Panel

A Django Admin panel for browsing, inspecting, and managing Django cache backends defined in your `CACHES` setting.

![Django Cache Panel - Instance List](https://raw.githubusercontent.com/yassi/dj-cache-panel/main/images/instances_list.png)

## Docs

[https://yassi.github.io/dj-cache-panel/](https://yassi.github.io/dj-cache-panel/)

## Features

- 🔍 **Browse Cache Instances**: View all configured cache backends from your `CACHES` setting
- 📊 **Abilities Matrix**: See at a glance which operations each cache supports (Query, Get, Delete, Flush)
- 🔎 **Key Search**: Search and browse cache keys with wildcard patterns (for supported backends)
- 📄 **Value Preview**: View cache values directly in search results
- 📑 **Pagination**: Navigate through large sets of keys efficiently
- 🎯 **Admin Integration**: Seamlessly integrates with Django's admin interface
- 🔒 **Secure**: Only accessible to staff users
- 🔌 **Backend Agnostic**: Works with any Django cache backend (with varying feature support)

## Supported Cache Data Types

- **String**: View and edit string values.


### Project Structure

```
dj-cache-panel/
├── dj_cache_panel/          # Main package
│   ├── templates/           # Django templates
│   ├── cache_utils.py       # Cache utilities
│   ├── views.py             # Django views
│   └── urls.py              # URL patterns
├── example_project/         # Example Django project
├── tests/                   # Test suite
├── images/                  # Screenshots for README
└── requirements.txt         # Development dependencies
```

## Requirements

- Python 3.9+
- Django 4.2+



## Screenshots

### Django Admin Integration
Seamlessly integrated into your Django admin interface. A new section for dj-cache-panel
will appear in the same places where your models appear.

**NOTE:** This application does not actually introduce any model or migrations.

![Admin Home](https://raw.githubusercontent.com/yassi/dj-cache-panel/main/images/admin_home.png)

### Caches Overview
Monitor your cache instances with detailed metrics and database information.

![Instance Overview](https://raw.githubusercontent.com/yassi/dj-cache-panel/main/images/instance_overview.png)


## Installation

### 1. Install the Package

```bash
pip install dj-cache-panel
```

### 2. Add to Django Settings

Add `dj_cache_panel` to your `INSTALLED_APPS`:

```python
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

### 3. Configure Cache Instances

Django cache panel will use the `CACHES` setting normally defined in django projects

```python
CACHES = {
    ...
}
```


### 4. Include URLs

Add the Cache Panel URLs to your main `urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/cache/', include('dj_cache_panel.urls')),  # Add this line
    path('admin/', admin.site.urls),
]
```

### 5. Run Migrations and Create Superuser

```bash
python manage.py migrate
python manage.py createsuperuser  # If you don't have an admin user
```

### 6. Access the Panel

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to the Django admin at `http://127.0.0.1:8000/admin/`

3. Look for the "DJ_CACHE_PANEL" section in the admin interface

4. Click "Manage Cache keys and values" to start browsing your cache instances



## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Development Setup

If you want to contribute to this project or set it up for local development:

### Prerequisites

- Python 3.9 or higher
- Redis server running locally
- Git
- Autoconf

### 1. Clone the Repository

```bash
git clone https://github.com/yassi/dj-cache-panel.git
cd dj-cache-panel
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dj-cache-panel inside of your virtualenv

A make file is included in the repository root with multiple commands for building
and maintaining this project. The best approach is to start by using one of the
package installation commands found below:
```bash
# Install all dependencies and dj-cache-panel into your current env
make install
```

### 4. Set Up Example Project

The repository includes an example Django project for development and testing:

```bash
cd example_project
python manage.py migrate
python manage.py createsuperuser
```

### 5. Populate Test Data (Optional)
An optional CLI tool for populating cache keys automatically is included in the
example django project in this code base.

```bash
python manage.py populate_redis
```

This command will populate your cache instance with sample data for testing.

### 6. Run the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin/` to access the Django admin with Cache Panel.

### 7. Running Tests

The project includes a comprehensive test suite. You can run them by using make or
by invoking pytest directly:

```bash
# build and install all dev dependencies and run all tests inside of docker container
make test

# Additionally generate coverage reports in multiple formats
make test_coverage
```

**Note**: Tests require a running cache backend (e.g., Redis) on `127.0.0.1:6379`. The tests use databases 13, 14, and 15 for isolation and automatically clean up after each test.

### 8. Dockerized Cache Backend

Test for this project (as well as any active development) require an active cache backend installation.
Although not required, a docker-compose file is included to allow for easy creation of local
cache instances using redis, memcached, local memory, etc.

```bash
# Start Redis on localhost and the usual port 6379
docker-compose up -d
```
