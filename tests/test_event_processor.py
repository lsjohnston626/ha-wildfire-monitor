"""Tests for transition-safe event detection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from custom_components.wildfire_monitor.const import (
    EVENT_EVACUATION_LEVEL_DECREASED,
    EVENT_EVACUATION_LEVEL_INCREASED,
    EVENT_FIRE_ENTERED_PERIMETER,
    EVENT_OFFICIAL_ALERT_ENDED,
    EVENT_OFFICIAL_ALERT_STARTED,
    EVENT_SOURCE_RECOVERED,
    EVENT_SOURCE_STALE,
    EVENT_THREAT_LEVEL_DECREASED,
    EVENT_THREAT_LEVEL_INCREASED,
    EVENT_WILDFIRE_DISCOVERED,
    EVENT_WILDFIRE_NO_LONGER_NEARBY,
)
from custom_components.wildfire_monitor.event_processor import WildfireEventDetector
from custom_components.wildfire_monitor.models import Alert, Fire


def _fire(
    fire_id: str,
    *,
    distance: float = 20,
    inside: bool = False,
    name: str = "Test Fire",
) -> Fire:
    return Fire(
        irwin_id=fire_id,
        name=name,
        distance_miles=distance,
        inside_perimeter=inside,
        acres=100,
        containment=20,
        incident_type="WF",
        discovered="2026-07-01",
        source_url=f"https://example.test/fires/{fire_id}",
    )


def _alert(
    alert_id: str,
    *,
    event: str = "Red Flag Warning",
    text: str = "",
) -> Alert:
    return Alert(
        alert_id=alert_id,
        event=event,
        headline=text or event,
        description=text,
        instruction=None,
        expires=datetime.now(UTC) + timedelta(hours=1),
        sender="NWS Test",
        severity="Severe",
        urgency="Immediate",
        certainty="Observed",
        source_url=f"https://example.test/alerts/{alert_id}",
    )


def _types(events) -> list[str]:
    return [event.event_type for event in events]


def _detector(
    fires: list[Fire] | None = None,
    alerts: list[Alert] | None = None,
) -> WildfireEventDetector:
    return WildfireEventDetector(
        fires or [],
        alerts or [],
        nifc_fresh=True,
        nws_fresh=True,
        nifc_initialized=True,
        nws_initialized=True,
    )


def test_new_fire_and_perimeter_transition_emit_events() -> None:
    detector = _detector([_fire("A")])

    events = detector.process_nifc(
        [_fire("A"), _fire("B", distance=0, inside=True, name="Critical Fire")],
        successful_refresh=True,
        is_fresh=True,
    )

    assert EVENT_WILDFIRE_DISCOVERED in _types(events)
    assert EVENT_FIRE_ENTERED_PERIMETER in _types(events)
    assert EVENT_THREAT_LEVEL_INCREASED in _types(events)
    discovered = next(
        event for event in events if event.event_type == EVENT_WILDFIRE_DISCOVERED
    )
    assert discovered.data["fire_id"] == "B"
    assert discovered.data["name"] == "Critical Fire"


def test_missing_fire_requires_two_successful_refreshes() -> None:
    detector = _detector([_fire("A"), _fire("B")])

    first = detector.process_nifc(
        [_fire("A")],
        successful_refresh=True,
        is_fresh=True,
    )
    second = detector.process_nifc(
        [_fire("A")],
        successful_refresh=True,
        is_fresh=True,
    )

    assert EVENT_WILDFIRE_NO_LONGER_NEARBY not in _types(first)
    assert EVENT_WILDFIRE_NO_LONGER_NEARBY in _types(second)


def test_temporarily_missing_fire_does_not_rediscover() -> None:
    detector = _detector([_fire("A")])
    detector.process_nifc([], successful_refresh=True, is_fresh=True)

    events = detector.process_nifc(
        [_fire("A")],
        successful_refresh=True,
        is_fresh=True,
    )

    assert EVENT_WILDFIRE_DISCOVERED not in _types(events)
    assert EVENT_WILDFIRE_NO_LONGER_NEARBY not in _types(events)


def test_temporarily_missing_fire_does_not_reenter_perimeter() -> None:
    detector = _detector([_fire("A", distance=0, inside=True)])
    detector.process_nifc([], successful_refresh=True, is_fresh=True)

    events = detector.process_nifc(
        [_fire("A", distance=0, inside=True)],
        successful_refresh=True,
        is_fresh=True,
    )

    assert EVENT_FIRE_ENTERED_PERIMETER not in _types(events)


def test_alert_and_evacuation_transitions_emit_events() -> None:
    detector = _detector()
    evacuation = _alert(
        "evac-1",
        event="Evacuation Immediate",
        text="Level 3 evacuation order. Leave immediately.",
    )

    started = detector.process_nws(
        [evacuation],
        successful_refresh=True,
        is_fresh=True,
    )
    ended = detector.process_nws(
        [],
        successful_refresh=True,
        is_fresh=True,
    )

    assert EVENT_OFFICIAL_ALERT_STARTED in _types(started)
    assert EVENT_EVACUATION_LEVEL_INCREASED in _types(started)
    assert EVENT_THREAT_LEVEL_INCREASED in _types(started)
    assert EVENT_OFFICIAL_ALERT_ENDED in _types(ended)
    assert EVENT_EVACUATION_LEVEL_DECREASED in _types(ended)
    assert EVENT_THREAT_LEVEL_DECREASED in _types(ended)


def test_source_stale_and_recovered_emit_once() -> None:
    detector = _detector()

    stale = detector.process_nifc(
        [],
        successful_refresh=False,
        is_fresh=False,
    )
    still_stale = detector.process_nifc(
        [],
        successful_refresh=False,
        is_fresh=False,
    )
    recovered = detector.process_nifc(
        [],
        successful_refresh=True,
        is_fresh=True,
    )

    assert _types(stale) == [EVENT_SOURCE_STALE]
    assert still_stale == []
    assert _types(recovered) == [EVENT_SOURCE_RECOVERED]


def test_first_successful_refresh_becomes_silent_baseline() -> None:
    detector = WildfireEventDetector(
        [],
        [],
        nifc_fresh=False,
        nws_fresh=True,
        nifc_initialized=False,
        nws_initialized=True,
    )

    initial = detector.process_nifc(
        [_fire("A", distance=0, inside=True)],
        successful_refresh=True,
        is_fresh=True,
    )
    next_refresh = detector.process_nifc(
        [
            _fire("A", distance=0, inside=True),
            _fire("B", distance=10),
        ],
        successful_refresh=True,
        is_fresh=True,
    )

    assert initial == []
    assert EVENT_WILDFIRE_DISCOVERED in _types(next_refresh)
