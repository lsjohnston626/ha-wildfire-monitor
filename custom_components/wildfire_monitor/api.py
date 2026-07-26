"""Clients and parsers for the NIFC WFIGS and NWS APIs."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    NIFC_INCIDENT_URL,
    NIFC_PERIMETER_URL,
    NWS_ALERTS_URL,
    USER_AGENT,
)
from .geometry import haversine_miles, polygon_distance_miles
from .models import Alert, Fire
from .rules import is_fire_alert


class WildfireApiError(Exception):
    """An upstream API request or response failed."""


def _first(attributes: dict[str, Any], *names: str) -> Any:
    """Get the first non-null field, case-insensitively."""
    folded = {key.casefold(): value for key, value in attributes.items()}
    for name in names:
        value = folded.get(name.casefold())
        if value is not None:
            return value
    return None


def _number(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _identifier(value: Any) -> str | None:
    if not value:
        return None
    return str(value).strip().strip("{}").casefold()


def parse_incidents(
    payload: dict[str, Any], latitude: float, longitude: float, radius: float
) -> list[Fire]:
    """Parse and filter WFIGS incident points."""
    fires: list[Fire] = []
    for feature in payload.get("features", []):
        attributes = feature.get("attributes") or feature.get("properties") or {}
        category = str(
            _first(
                attributes,
                "IncidentTypeCategory",
                "attr_IncidentTypeCategory",
                "IncidentTypeKind",
            )
            or ""
        ).upper()
        incident_type = str(
            _first(attributes, "IncidentType", "attr_IncidentType") or category
        )
        if (
            category not in {"WF", "CX"}
            and "WILDFIRE" not in incident_type.upper()
            and ("COMPLEX" not in incident_type.upper())
        ):
            continue
        if category == "RX" or "PRESCRIB" in incident_type.upper():
            continue
        geometry = feature.get("geometry") or {}
        lon = _number(geometry.get("x"))
        lat = _number(geometry.get("y"))
        if lon is None or lat is None:
            coordinates = geometry.get("coordinates") or []
            if len(coordinates) >= 2:
                lon, lat = _number(coordinates[0]), _number(coordinates[1])
        if lon is None or lat is None:
            continue
        distance = haversine_miles(latitude, longitude, lat, lon)
        if distance > radius:
            continue
        irwin_id = _identifier(
            _first(attributes, "IrwinID", "IRWINID", "attr_IrwinID", "GlobalID")
        )
        fires.append(
            Fire(
                irwin_id=irwin_id,
                name=str(
                    _first(
                        attributes,
                        "IncidentName",
                        "attr_IncidentName",
                        "poly_IncidentName",
                    )
                    or "Unnamed wildfire"
                ),
                distance_miles=distance,
                acres=_number(
                    _first(
                        attributes,
                        "DailyAcres",
                        "IncidentSize",
                        "CalculatedAcres",
                        "attr_DailyAcres",
                    )
                ),
                containment=_number(
                    _first(
                        attributes,
                        "PercentContained",
                        "PercentContainment",
                        "attr_PercentContained",
                    )
                ),
                incident_type=incident_type or None,
                discovered=_first(
                    attributes,
                    "FireDiscoveryDateTime",
                    "attr_FireDiscoveryDateTime",
                ),
                source_url=(
                    f"https://irwin.doi.gov/observer/?id={irwin_id}"
                    if irwin_id
                    else None
                ),
            )
        )
    return fires


def join_perimeters(
    fires: list[Fire],
    payload: dict[str, Any],
    latitude: float,
    longitude: float,
    radius: float,
) -> list[Fire]:
    """Join nearby perimeter geometry to incidents and apply edge distance."""
    by_id = {fire.irwin_id: fire for fire in fires if fire.irwin_id}
    for feature in payload.get("features", []):
        attributes = feature.get("attributes") or feature.get("properties") or {}
        category = str(
            _first(attributes, "IncidentTypeCategory", "attr_IncidentTypeCategory")
            or ""
        ).upper()
        if category == "RX":
            continue
        geometry = feature.get("geometry") or {}
        inside, distance = polygon_distance_miles(latitude, longitude, geometry)
        if distance > radius and not inside:
            continue
        irwin_id = _identifier(
            _first(
                attributes,
                "IrwinID",
                "attr_IrwinID",
                "poly_IRWINID",
                "SourceGlobalID",
                "attr_SourceGlobalID",
                "poly_SourceGlobalID",
            )
        )
        fire = by_id.get(irwin_id)
        if fire:
            fire.inside_perimeter = inside
            fire.distance_miles = min(fire.distance_miles, distance)
            fire.acres = fire.acres or _number(
                _first(
                    attributes,
                    "GISAcres",
                    "CalculatedAcres",
                    "IncidentSize",
                    "poly_GISAcres",
                    "attr_CalculatedAcres",
                    "attr_IncidentSize",
                )
            )
            continue
        fire = Fire(
            irwin_id=irwin_id,
            name=str(
                _first(attributes, "IncidentName", "poly_IncidentName")
                or "Unnamed wildfire"
            ),
            distance_miles=distance,
            inside_perimeter=inside,
            acres=_number(
                _first(
                    attributes,
                    "GISAcres",
                    "CalculatedAcres",
                    "IncidentSize",
                    "poly_GISAcres",
                    "attr_CalculatedAcres",
                    "attr_IncidentSize",
                )
            ),
            containment=_number(
                _first(attributes, "PercentContained", "attr_PercentContained")
            ),
            incident_type=category or "WF",
        )
        fires.append(fire)
        if irwin_id:
            by_id[irwin_id] = fire
    return sorted(fires, key=lambda fire: fire.distance_miles)


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_nws_alerts(payload: dict[str, Any]) -> list[Alert]:
    """Parse fire-relevant official NWS alert features."""
    alerts: list[Alert] = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        alert = Alert(
            alert_id=str(feature.get("id") or properties.get("id") or ""),
            event=str(properties.get("event") or "Unknown"),
            headline=properties.get("headline"),
            description=properties.get("description"),
            instruction=properties.get("instruction"),
            expires=_parse_datetime(
                properties.get("expires") or properties.get("ends")
            ),
            sender=properties.get("senderName") or properties.get("sender"),
            severity=str(properties.get("severity") or "Unknown"),
            urgency=str(properties.get("urgency") or "Unknown"),
            certainty=str(properties.get("certainty") or "Unknown"),
            source_url=(
                properties.get("@id") or feature.get("id") or properties.get("web")
            ),
        )
        if is_fire_alert(alert):
            alerts.append(alert)
    urgency = {"Immediate": 0, "Expected": 1, "Future": 2, "Past": 3, "Unknown": 4}
    severity = {"Extreme": 0, "Severe": 1, "Moderate": 2, "Minor": 3, "Unknown": 4}
    return sorted(
        alerts,
        key=lambda alert: (
            urgency.get(alert.urgency, 4),
            severity.get(alert.severity, 4),
        ),
    )


class NifcClient:
    """Fetch NIFC WFIGS incidents and perimeters."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def async_get_fires(
        self, latitude: float, longitude: float, radius: float
    ) -> list[Fire]:
        params = {
            "f": "json",
            "where": "1=1",
            "geometry": f"{longitude},{latitude}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "distance": str(radius),
            "units": "esriSRUnit_StatuteMile",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
        }
        incidents, perimeters = await asyncio.gather(
            self._get(NIFC_INCIDENT_URL, params),
            self._get(NIFC_PERIMETER_URL, params),
        )
        fires = parse_incidents(incidents, latitude, longitude, radius)
        return join_perimeters(fires, perimeters, latitude, longitude, radius)

    async def _get(self, url: str, params: dict[str, str]) -> dict[str, Any]:
        try:
            async with self._session.get(url, params=params, timeout=30) as response:
                response.raise_for_status()
                payload = await response.json()
        except (ClientError, TimeoutError, ValueError) as err:
            raise WildfireApiError(str(err)) from err
        if "error" in payload:
            raise WildfireApiError(str(payload["error"]))
        return payload


class NwsClient:
    """Fetch point-specific NWS alerts."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def async_get_alerts(self, latitude: float, longitude: float) -> list[Alert]:
        try:
            async with self._session.get(
                NWS_ALERTS_URL,
                params={"point": f"{latitude},{longitude}", "status": "actual"},
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/geo+json",
                },
                timeout=30,
            ) as response:
                response.raise_for_status()
                payload = await response.json()
        except (ClientError, TimeoutError, ValueError) as err:
            raise WildfireApiError(str(err)) from err
        return parse_nws_alerts(payload)
