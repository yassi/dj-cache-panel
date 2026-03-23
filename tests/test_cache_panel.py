"""
Tests for dj_cache_panel.cache_panel (e.g. get_cache_panel with dotted panel paths).
"""

from unittest.mock import patch

from django.test import SimpleTestCase

from dj_cache_panel import cache_panel
from dj_cache_panel.cache_panel import get_cache_panel, GenericCachePanel
from example_project.backends import ExamplePanel

EXAMPLE_DUMMY_BACKEND = "example_project.backends.ExampleDummyCache"


class TestGetCachePanelDynamicImport(SimpleTestCase):
    """Panel class given as a full module path (see example_project.backends)."""

    def test_loads_panel_via_full_module_path(self):
        """BACKEND_PANEL_EXTENSIONS dotted path resolves through import_module."""
        panel = get_cache_panel("example_dynamic_panel")
        self.assertIsInstance(panel, ExamplePanel)
        self.assertEqual(panel.cache_name, "example_dynamic_panel")

    def test_dynamic_import_missing_class_wraps_as_import_error(self):
        """Class missing from module: AttributeError becomes ImportError with context."""
        with patch.dict(
            cache_panel.BACKEND_PANEL_MAP,
            {EXAMPLE_DUMMY_BACKEND: "example_project.backends.NonexistentPanelClass"},
        ):
            with self.assertRaises(ImportError) as ctx:
                get_cache_panel("example_dynamic_panel")

        msg = str(ctx.exception)
        self.assertIn("Failed to import panel class", msg)
        self.assertIn("NonexistentPanelClass", msg)
        self.assertIn("not found in module", msg)

    def test_dynamic_import_bad_module_wraps_as_import_error(self):
        """ImportError from import_module is re-wrapped with a consistent prefix."""
        with patch.dict(
            cache_panel.BACKEND_PANEL_MAP,
            {EXAMPLE_DUMMY_BACKEND: "nonexistent_module_xyz.SomePanel"},
        ):
            with self.assertRaises(ImportError) as ctx:
                get_cache_panel("example_dynamic_panel")

        self.assertIn("Failed to import panel class", str(ctx.exception))

    def test_dynamic_import_valueerror_wraps_as_import_error(self):
        """ValueError inside the try block is wrapped like other failures."""
        with patch.dict(
            cache_panel.BACKEND_PANEL_MAP,
            {EXAMPLE_DUMMY_BACKEND: "example_project.backends.ExamplePanel"},
        ):
            with patch(
                "importlib.import_module", side_effect=ValueError("invalid module path")
            ):
                with self.assertRaises(ImportError) as ctx:
                    get_cache_panel("example_dynamic_panel")

        self.assertIn("Failed to import panel class", str(ctx.exception))
        self.assertIn("invalid module path", str(ctx.exception))

    def test_generic_panel_fallback(self):
        """If no panel class is found for a backend, a generic panel is returned."""
        with patch.dict(cache_panel.BACKEND_PANEL_MAP, {}):
            panel = get_cache_panel("example_dynamic_panel")
            self.assertIsInstance(panel, GenericCachePanel)
            self.assertEqual(panel.cache_name, "example_dynamic_panel")
