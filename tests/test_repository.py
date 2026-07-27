"""Repository metadata checks."""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.wildfire_monitor.const import DOMAIN, VERSION

ROOT = Path(__file__).parents[1]
INTEGRATION_DIR = ROOT / "custom_components" / DOMAIN


def test_release_metadata_is_consistent() -> None:
    """Keep the runtime and HACS-visible versions synchronized."""
    manifest = json.loads(
        (INTEGRATION_DIR / "manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["domain"] == DOMAIN
    assert manifest["version"] == VERSION


def test_hacs_metadata_declares_us_scope() -> None:
    """Keep the HACS listing explicit about geographic coverage."""
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))

    assert hacs["name"] == "Wildfire Monitor (US)"
    assert hacs["country"] == "US"
