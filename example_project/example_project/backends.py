"""
Example cache backend and panel for exercising full module path panel resolution.

The cache backend is a thin subclass of Django's DummyCache so it has a unique
``BACKEND`` import path. The panel subclasses ``DummyCachePanel`` and is wired via
``DJ_CACHE_PANEL_SETTINGS["BACKEND_PANEL_EXTENSIONS"]`` using that dotted path.

NOTE: This is not a real cache backend; it is only used for testing. pay no mind.
It is used to test the ability to dynamically import a panel class from a full module path.
"""

from django.core.cache.backends.dummy import DummyCache

from dj_cache_panel.cache_panel import DummyCachePanel


class ExampleDummyCache(DummyCache):
    """Behaves like DummyCache; exists to provide a distinct backend module path."""

    pass


class ExamplePanel(DummyCachePanel):
    """Loaded via ``example_project.backends.ExamplePanel`` in the panel map."""

    pass
