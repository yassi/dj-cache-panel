# Installation

## 1. Install the Package

```bash
pip install dj-cache-panel
```

### Optional: Valkey Support

To enable support for the **Valkey** cache backend, install the optional dependency:

```bash
pip install dj-cache-panel[valkey]
```

**Requirements:**
- Python 3.9-3.14
- The `django-valkey` package will be installed automatically

**What You Get:**
- Support for Valkey cache backend in the Cache Panel
- Ability to browse, search, and manage Valkey cache keys
- Full feature parity with Redis cache panel

If you don't need Valkey support, the base installation (`pip install dj-cache-panel`) works perfectly fine.

## 2. Add to Django Settings

Add `dj_cache_panel` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dj_cache_panel',  # Add this
    # ... your other apps
]
```

## 3. Include URLs

Add the Cache Panel URLs to your main `urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/dj-cache-panel/', include('dj_cache_panel.urls')),
    path('admin/', admin.site.urls),
]
```

## 4. Run Migrations

```bash
python manage.py migrate
```

## 5. Access the Panel

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to `http://127.0.0.1:8000/admin/`

3. Look for the "DJ_CACHE_PANEL" section

4. Click "Manage Cache keys and values"

That's it! No additional configuration required. Django Cache Panel will automatically detect all cache backends defined in your `CACHES` setting.
