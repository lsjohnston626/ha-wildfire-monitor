"""Pure transition detection for Wildfire Monitor events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .const import (
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
from .models import Alert, Fire
from .rules import evacuation_level, threat_level

_THREAT_RANK = {
    "none": 0,
    "low": 1,
    "moderate": 2,
    "high": 3,
    "extreme": 4,
}
_EVACUATION_RANK = {
    "none": 0,
    "unclassified": 1,
    "level_1_ready": 2,
    "level_2_set": 3,
    "level_3_go": 4,
}


@dataclass(frozen=True, slots=True)
class MonitorEvent:
    """One event entity occurrence."""

    event_type: str
    data: dict[str, Any]


def _fire_id(fire: Fire) -> str:
    """Return the most stable available identity for a fire."""
    if fire.irwin_id:
        return fire.irwin_id
    if fire.source_url:
        return fire.source_url
    return "|".join(
        (
            fire.name.strip().casefold(),
            fire.discovered or "",
            fire.incident_type or "",
        )
    )


def _alert_id(alert: Alert) -> str:
    """Return the most stable available identity for an alert."""
    if alert.alert_id:
        return alert.alert_id
    if alert.source_url:
        return alert.source_url
    return "|".join(
        (
            alert.event.strip().casefold(),
            alert.headline or "",
            alert.sender or "",
        )
    )


def _fire_data(fire_id: str, fire: Fire) -> dict[str, Any]:
    return {"source": "nifc", "fire_id": fire_id, **fire.as_attribute()}


def _alert_data(alert_id: str, alert: Alert) -> dict[str, Any]:
    return {"source": "nws", "alert_id": alert_id, **alert.as_attribute()}


class WildfireEventDetector:
    """Detect meaningful transitions without emitting events on initial data."""

    def __init__(
        self,
        fires: list[Fire],
        alerts: list[Alert],
        *,
        nifc_fresh: bool,
        nws_fresh: bool,
        nifc_initialized: bool,
        nws_initialized: bool,
    ) -> None:
        self._fires = {_fire_id(fire): fire for fire in fires}
        self._alerts = {_alert_id(alert): alert for alert in alerts}
        self._missing_fires: dict[str, tuple[Fire, int]] = {}
        self._nifc_fresh = nifc_fresh
        self._nws_fresh = nws_fresh
        self._nifc_initialized = nifc_initialized
        self._nws_initialized = nws_initialized
        self._stale_announced = {"nifc": False, "nws": False}
        self._threat_level = self._current_threat_level()
        self._evacuation_level = evacuation_level(list(self._alerts.values()))

    def process_nifc(
        self,
        fires: list[Fire],
        *,
        successful_refresh: bool,
        is_fresh: bool,
    ) -> list[MonitorEvent]:
        """Process one NIFC coordinator notification."""
        if not self._nifc_initialized:
            self._nifc_fresh = is_fresh
            if not successful_refresh:
                return []
            self._fires = {_fire_id(fire): fire for fire in fires}
            self._nifc_initialized = True
            self._reset_levels()
            return []

        events = self._freshness_events("nifc", is_fresh)
        if successful_refresh:
            events.extend(self._fire_events(fires))
        events.extend(self._level_events())
        return events

    def process_nws(
        self,
        alerts: list[Alert],
        *,
        successful_refresh: bool,
        is_fresh: bool,
    ) -> list[MonitorEvent]:
        """Process one NWS coordinator notification."""
        if not self._nws_initialized:
            self._nws_fresh = is_fresh
            if not successful_refresh:
                return []
            self._alerts = {_alert_id(alert): alert for alert in alerts}
            self._nws_initialized = True
            self._reset_levels()
            return []

        events = self._freshness_events("nws", is_fresh)
        if successful_refresh:
            events.extend(self._alert_events(alerts))
        events.extend(self._level_events())
        return events

    def _freshness_events(self, source: str, is_fresh: bool) -> list[MonitorEvent]:
        current = self._nifc_fresh if source == "nifc" else self._nws_fresh
        if source == "nifc":
            self._nifc_fresh = is_fresh
        else:
            self._nws_fresh = is_fresh

        if current and not is_fresh:
            self._stale_announced[source] = True
            return [MonitorEvent(EVENT_SOURCE_STALE, {"source": source})]
        if not current and is_fresh and self._stale_announced[source]:
            self._stale_announced[source] = False
            return [MonitorEvent(EVENT_SOURCE_RECOVERED, {"source": source})]
        return []

    def _fire_events(self, fires: list[Fire]) -> list[MonitorEvent]:
        current = {_fire_id(fire): fire for fire in fires}
        events: list[MonitorEvent] = []
        missing_before = set(self._missing_fires)

        for fire_id, fire in current.items():
            previous = self._fires.get(fire_id)
            if previous is None and fire_id not in missing_before:
                events.append(
                    MonitorEvent(
                        EVENT_WILDFIRE_DISCOVERED,
                        _fire_data(fire_id, fire),
                    )
                )
            if fire.inside_perimeter and (
                previous is None or not previous.inside_perimeter
            ):
                events.append(
                    MonitorEvent(
                        EVENT_FIRE_ENTERED_PERIMETER,
                        _fire_data(fire_id, fire),
                    )
                )
            self._missing_fires.pop(fire_id, None)

        for fire_id in self._fires.keys() - current.keys():
            self._missing_fires.setdefault(fire_id, (self._fires[fire_id], 0))

        for fire_id, (fire, missing_count) in list(self._missing_fires.items()):
            missing_count += 1
            if missing_count >= 2:
                events.append(
                    MonitorEvent(
                        EVENT_WILDFIRE_NO_LONGER_NEARBY,
                        _fire_data(fire_id, fire),
                    )
                )
                del self._missing_fires[fire_id]
            else:
                self._missing_fires[fire_id] = (fire, missing_count)

        self._fires = current
        return events

    def _alert_events(self, alerts: list[Alert]) -> list[MonitorEvent]:
        current = {_alert_id(alert): alert for alert in alerts}
        events = [
            MonitorEvent(
                EVENT_OFFICIAL_ALERT_STARTED,
                _alert_data(alert_id, current[alert_id]),
            )
            for alert_id in current.keys() - self._alerts.keys()
        ]
        events.extend(
            MonitorEvent(
                EVENT_OFFICIAL_ALERT_ENDED,
                _alert_data(alert_id, self._alerts[alert_id]),
            )
            for alert_id in self._alerts.keys() - current.keys()
        )
        self._alerts = current
        return events

    def _current_threat_level(self) -> str | None:
        return threat_level(
            list(self._fires.values()),
            list(self._alerts.values()),
            self._nifc_fresh,
            self._nws_fresh,
        )

    def _level_events(self) -> list[MonitorEvent]:
        events: list[MonitorEvent] = []
        current_threat = self._current_threat_level()
        if (
            current_threat != self._threat_level
            and current_threat is not None
            and self._threat_level is not None
        ):
            event_type = (
                EVENT_THREAT_LEVEL_INCREASED
                if _THREAT_RANK[current_threat] > _THREAT_RANK[self._threat_level]
                else EVENT_THREAT_LEVEL_DECREASED
            )
            events.append(
                MonitorEvent(
                    event_type,
                    {
                        "source": "combined",
                        "previous_level": self._threat_level,
                        "level": current_threat,
                    },
                )
            )
        self._threat_level = current_threat

        current_evacuation = evacuation_level(list(self._alerts.values()))
        if current_evacuation != self._evacuation_level:
            event_type = (
                EVENT_EVACUATION_LEVEL_INCREASED
                if _EVACUATION_RANK[current_evacuation]
                > _EVACUATION_RANK[self._evacuation_level]
                else EVENT_EVACUATION_LEVEL_DECREASED
            )
            events.append(
                MonitorEvent(
                    event_type,
                    {
                        "source": "nws",
                        "previous_level": self._evacuation_level,
                        "level": current_evacuation,
                    },
                )
            )
        self._evacuation_level = current_evacuation
        return events

    def _reset_levels(self) -> None:
        self._threat_level = self._current_threat_level()
        self._evacuation_level = evacuation_level(list(self._alerts.values()))
