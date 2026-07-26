"""Evacuation and threat rules."""

from datetime import UTC, datetime, timedelta

import pytest

from custom_components.wildfire_monitor.models import Alert, Fire
from custom_components.wildfire_monitor.rules import (
    evacuation_level,
    evacuation_status,
    threat_level,
    unexpired,
)


def alert(event="Local Area Emergency", text="", expires=None):
    return Alert(
        alert_id="1",
        event=event,
        headline=text,
        description=None,
        instruction=None,
        expires=expires,
        sender="NWS",
        severity="Severe",
        urgency="Immediate",
        certainty="Observed",
        source_url="https://example.test",
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Evacuation Level 1 for Pine Road", "level_1_ready"),
        ("Evacuation area: Be Ready", "level_1_ready"),
        ("Evacuation Level 2", "level_2_set"),
        ("Evacuation area: Be Set", "level_2_set"),
        ("Evacuation Level 3", "level_3_go"),
        ("Evacuate: Go Now", "level_3_go"),
        ("Evacuation: leave immediately", "level_3_go"),
        ("Evacuation advisory is in effect", "unclassified"),
    ],
)
def test_evacuation_phrase_mapping(text, expected) -> None:
    assert evacuation_level([alert(text=text)]) == expected


def test_ready_without_evacuation_context_is_not_level() -> None:
    assert evacuation_level([alert(text="Be ready for thunderstorms")]) == "none"


def test_evacuation_immediate_event_and_order() -> None:
    assert evacuation_level([alert(event="Evacuation Immediate")]) == "level_3_go"
    assert (
        evacuation_level([alert(text="An evacuation order is in effect")])
        == "level_3_go"
    )


def test_highest_conflicting_level_wins() -> None:
    assert (
        evacuation_level(
            [alert(text="Evacuation Level 1"), alert(text="Evacuation Level 3")]
        )
        == "level_3_go"
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Evacuation advisory", "advisory"),
        ("Evacuation warning", "warning"),
        ("Evacuation order", "order"),
        ("Evacuation: Go Now", "immediate"),
        ("Evacuation notice", "unknown"),
    ],
)
def test_evacuation_status_terms(text, expected) -> None:
    assert evacuation_status([alert(text=text)]) == expected


@pytest.mark.parametrize(
    ("distance", "expected"),
    [(5, "high"), (5.001, "moderate"), (15, "moderate"), (15.001, "low")],
)
def test_threat_distance_boundaries(distance, expected) -> None:
    fire = Fire(None, "Fire", distance)
    assert threat_level([fire], [], True, True) == expected


def test_extreme_and_alert_threats() -> None:
    assert threat_level([Fire(None, "Fire", 30, True)], [], True, True) == "extreme"
    assert threat_level([], [alert(event="Fire Warning")], True, True) == "high"
    assert threat_level([], [alert(event="Red Flag Warning")], True, True) == "moderate"


def test_proximity_never_infers_evacuation() -> None:
    assert evacuation_level([]) == "none"
    assert evacuation_status([]) == "none"
    assert threat_level([Fire(None, "Fire", 1)], [], True, True) == "high"


def test_stale_sources_never_reassure() -> None:
    assert threat_level([], [], False, True) is None
    assert threat_level([], [], True, False) is None
    assert threat_level([], [], True, True) == "none"


def test_positive_cached_alert_survives_stale_source() -> None:
    assert threat_level([], [alert(event="Fire Warning")], False, False) == "high"


def test_expired_cached_alerts_are_removed() -> None:
    now = datetime.now(UTC)
    alerts = [
        alert(expires=now - timedelta(seconds=1)),
        alert(expires=now + timedelta(seconds=1)),
        alert(expires=None),
    ]
    assert len(unexpired(alerts, now)) == 2
