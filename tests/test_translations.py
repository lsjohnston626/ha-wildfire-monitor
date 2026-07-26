"""Tests for bundled translations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

INTEGRATION_DIR = Path(__file__).parents[1] / "custom_components" / "wildfire_monitor"
TRANSLATIONS_DIR = INTEGRATION_DIR / "translations"
EXPECTED_LOCALES = {
    "de",
    "en",
    "es",
    "fr",
    "it",
    "nl",
    "pl",
    "pt",
    "ru",
    "sv",
    "zh-Hans",
}


def _leaf_paths(value: Any, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    """Return every translated leaf path in a nested mapping."""
    if isinstance(value, dict):
        return {
            path
            for key, child in value.items()
            for path in _leaf_paths(child, (*prefix, key))
        }
    assert isinstance(value, str)
    assert value.strip()
    return {prefix}


def test_translation_files_match_english_schema() -> None:
    """Every locale should provide every English translation key."""
    files = {path.stem: path for path in TRANSLATIONS_DIR.glob("*.json")}
    assert set(files) == EXPECTED_LOCALES

    english = json.loads(files["en"].read_text(encoding="utf-8"))
    english_paths = _leaf_paths(english)

    for locale, path in files.items():
        translation = json.loads(path.read_text(encoding="utf-8"))
        assert _leaf_paths(translation) == english_paths, locale


def test_custom_integration_does_not_ship_core_strings_file() -> None:
    """Custom integrations load complete strings from translations."""
    assert not (INTEGRATION_DIR / "strings.json").exists()
