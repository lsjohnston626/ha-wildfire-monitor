"""Tests for bundled translations."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

INTEGRATION_DIR = Path(__file__).parents[1] / "custom_components" / "wildfire_monitor"
TRANSLATIONS_DIR = INTEGRATION_DIR / "translations"
EXPECTED_LOCALES = {
    "af",
    "ar",
    "bg",
    "bn",
    "bs",
    "ca",
    "cs",
    "cy",
    "da",
    "de",
    "el",
    "en",
    "en-GB",
    "eo",
    "es",
    "es-419",
    "et",
    "eu",
    "fa",
    "fi",
    "fy",
    "fr",
    "ga",
    "gl",
    "gsw",
    "he",
    "hi",
    "hr",
    "hu",
    "hy",
    "id",
    "is",
    "it",
    "ja",
    "ka",
    "ko",
    "lb",
    "lt",
    "lv",
    "mk",
    "ml",
    "nb",
    "nl",
    "nn",
    "pl",
    "pt",
    "pt-BR",
    "ro",
    "ru",
    "sk",
    "sl",
    "sq",
    "sr",
    "sr-Latn",
    "sv",
    "ta",
    "te",
    "th",
    "tr",
    "uk",
    "ur",
    "vi",
    "zh-Hans",
    "zh-Hant",
}
EXPECTED_TRIGGER_TYPES = {
    "wildfire_discovered",
    "wildfire_no_longer_nearby",
    "fire_entered_perimeter",
    "official_alert_started",
    "official_alert_ended",
    "threat_level_increased",
    "threat_level_decreased",
    "evacuation_level_increased",
    "evacuation_level_decreased",
    "source_stale",
    "source_recovered",
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
        text = path.read_text(encoding="utf-8")
        translation = json.loads(text)
        assert _leaf_paths(translation) == english_paths, locale
        assert translation["title"] == "Wildfire Monitor", locale
        assert "NIFC" in text, locale
        assert "NWS" in text, locale
        assert "\ufffd" not in text, locale
        assert not re.search(r"\[\[\w*\d{3}\]\]", text), locale
        assert (
            set(translation["device_automation"]["trigger_type"])
            == EXPECTED_TRIGGER_TYPES
        ), locale


def test_custom_integration_does_not_ship_core_strings_file() -> None:
    """Custom integrations load complete strings from translations."""
    assert not (INTEGRATION_DIR / "strings.json").exists()
