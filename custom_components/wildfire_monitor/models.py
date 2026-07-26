"""Data models for Wildfire Monitor."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Fire:
    """A nearby wildfire."""

    irwin_id: str | None
    name: str
    distance_miles: float
    inside_perimeter: bool = False
    acres: float | None = None
    containment: float | None = None
    incident_type: str | None = None
    discovered: str | None = None
    source_url: str | None = None

    def as_attribute(self) -> dict[str, Any]:
        """Return a safe entity-attribute representation."""
        return {
            "irwin_id": self.irwin_id,
            "name": self.name,
            "distance_miles": round(self.distance_miles, 2),
            "inside_perimeter": self.inside_perimeter,
            "acres": self.acres,
            "containment": self.containment,
            "incident_type": self.incident_type,
            "discovered": self.discovered,
            "source_url": self.source_url,
        }


@dataclass(slots=True)
class Alert:
    """An official NWS alert."""

    alert_id: str
    event: str
    headline: str | None
    description: str | None
    instruction: str | None
    expires: datetime | None
    sender: str | None
    severity: str
    urgency: str
    certainty: str
    source_url: str | None

    @property
    def text(self) -> str:
        """Return all text used by conservative classification."""
        return "\n".join(
            part
            for part in (self.event, self.headline, self.description, self.instruction)
            if part
        )

    def as_attribute(self) -> dict[str, Any]:
        """Return the official alert fields for entity attributes."""
        return {
            "alert_id": self.alert_id,
            "event": self.event,
            "headline": self.headline,
            "description": self.description,
            "instruction": self.instruction,
            "expires": self.expires.isoformat() if self.expires else None,
            "sender": self.sender,
            "severity": self.severity,
            "urgency": self.urgency,
            "certainty": self.certainty,
            "source_url": self.source_url,
        }


@dataclass(slots=True)
class SourceData:
    """Cached coordinator source data."""

    records: list[Any] = field(default_factory=list)
    last_success: datetime | None = None
