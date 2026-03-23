"""
Tests for dj_cache_panel.cache_panel (e.g. get_cache_panel with dotted panel paths).
"""

from django.test import SimpleTestCase

from dj_cache_panel.cache_panel import get_cache_panel
from example_project.backends import ExamplePanel


class TestGetCachePanelDynamicImport(SimpleTestCase):
    """Panel class given as a full module path (see example_project.backends)."""

    def test_loads_panel_via_full_module_path(self):
        """BACKEND_PANEL_EXTENSIONS dotted path resolves through import_module."""
        panel = get_cache_panel("example_dynamic_panel")
        self.assertIsInstance(panel, ExamplePanel)
        self.assertEqual(panel.cache_name, "example_dynamic_panel")
