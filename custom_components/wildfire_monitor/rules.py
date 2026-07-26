"""Conservative wildfire and evacuation classification rules."""

from __future__ import annotations

import re
from datetime import datetime

from .models import Alert, Fire

FIRE_EVENTS = {
    "Fire Warning",
    "Red Flag Warning",
    "Fire Weather Watch",
    "Extreme Fire Danger",
    "Evacuation Immediate",
}
EVACUATION_CONTEXT = re.compile(
    r"\bevacuat(?:e|ion|ing)|\bready,?\s*set,?\s*go\b", re.I
)
LEVEL_3 = re.compile(
    r"\blevel\s*(?:3|three)\b|\bgo\s+now\b|\bleave\s+immediately\b", re.I
)
LEVEL_2 = re.compile(r"\blevel\s*(?:2|two)\b", re.I)
LEVEL_1 = re.compile(r"\blevel\s*(?:1|one)\b", re.I)


def is_fire_alert(alert: Alert) -> bool:
    """Return whether an alert is relevant to fire or evacuation."""
    return alert.event in FIRE_EVENTS or bool(
        re.search(r"\b(?:wildfire|fire weather|red flag|evacuat)", alert.text, re.I)
    )


def is_evacuation_alert(alert: Alert) -> bool:
    """Return whether an alert carries official evacuation content."""
    return alert.event == "Evacuation Immediate" or bool(
        EVACUATION_CONTEXT.search(alert.text)
    )


def evacuation_level(alerts: list[Alert]) -> str:
    """Derive the highest explicit Washington-style evacuation level."""
    best = 0
    has_evacuation = False
    for alert in alerts:
        text = alert.text
        if not is_evacuation_alert(alert):
            continue
        has_evacuation = True
        if (
            alert.event == "Evacuation Immediate"
            or LEVEL_3.search(text)
            or re.search(r"\bevacuation\s+order\b", text, re.I)
        ):
            best = max(best, 3)
        if LEVEL_2.search(text) or re.search(r"\bbe\s+set\b", text, re.I):
            best = max(best, 2)
        if LEVEL_1.search(text) or re.search(r"\bbe\s+ready\b", text, re.I):
            best = max(best, 1)
    return {1: "level_1_ready", 2: "level_2_set", 3: "level_3_go"}.get(best) or (
        "unclassified" if has_evacuation else "none"
    )


def evacuation_status(alerts: list[Alert]) -> str:
    """Preserve broader official evacuation terminology."""
    best = -2
    for alert in alerts:
        if not is_evacuation_alert(alert):
            continue
        text = alert.text
        if alert.event == "Evacuation Immediate" or re.search(
            r"\b(?:go now|leave immediately|evacuation immediate)\b", text, re.I
        ):
            best = max(best, 4)
        elif re.search(r"\bevacuation\s+order\b", text, re.I):
            best = max(best, 3)
        elif re.search(r"\bevacuation\s+warning\b", text, re.I):
            best = max(best, 2)
        elif re.search(r"\bevacuation\s+advisory\b", text, re.I):
            best = max(best, 1)
        else:
            best = max(best, -1)
    return {
        4: "immediate",
        3: "order",
        2: "warning",
        1: "advisory",
        -1: "unknown",
        -2: "none",
    }[best]


def threat_level(
    fires: list[Fire],
    alerts: list[Alert],
    nifc_fresh: bool,
    nws_fresh: bool,
) -> str | None:
    """Calculate threat; None represents an unsafe unknown/stale state."""
    evac_level = evacuation_level(alerts)
    evac_status = evacuation_status(alerts)
    events = {alert.event for alert in alerts}
    nearest = min((fire.distance_miles for fire in fires), default=float("inf"))
    if (
        any(fire.inside_perimeter for fire in fires)
        or evac_level == "level_3_go"
        or evac_status in {"order", "immediate"}
    ):
        return "extreme"
    if nearest <= 5 or evac_level == "level_2_set" or "Fire Warning" in events:
        return "high"
    if (
        nearest <= 15
        or evac_level == "level_1_ready"
        or evac_status == "warning"
        or events & {"Red Flag Warning", "Extreme Fire Danger", "Fire Weather Watch"}
    ):
        return "moderate"
    if fires:
        return "low"
    if nifc_fresh and nws_fresh:
        return "none"
    return None


def unexpired(alerts: list[Alert], now: datetime) -> list[Alert]:
    """Discard expired cached alerts."""
    return [alert for alert in alerts if alert.expires is None or alert.expires > now]
