"""Test setup that lets pure modules run without installing Home Assistant."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parents[1]

if importlib.util.find_spec("homeassistant") is None:
    custom_components = types.ModuleType("custom_components")
    custom_components.__path__ = [str(ROOT / "custom_components")]
    package = types.ModuleType("custom_components.wildfire_monitor")
    package.__path__ = [str(ROOT / "custom_components" / "wildfire_monitor")]
    sys.modules["custom_components"] = custom_components
    sys.modules["custom_components.wildfire_monitor"] = package
else:
    import pytest

    @pytest.fixture(autouse=True)
    def auto_enable_custom_integrations(enable_custom_integrations):
        """Allow Home Assistant to discover this custom integration in tests."""
        with patch(
            "custom_components.wildfire_monitor.async_setup_entry",
            return_value=True,
        ):
            yield
