"""Dependency-free spherical geometry helpers."""

from __future__ import annotations

from itertools import pairwise
from math import asin, atan2, cos, radians, sin, sqrt
from typing import Any

EARTH_RADIUS_MILES = 3958.7613


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in miles."""
    p1, p2 = radians(lat1), radians(lat2)
    dp = radians(lat2 - lat1)
    dl = radians(lon2 - lon1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * asin(min(1.0, sqrt(a)))


def point_in_ring(lat: float, lon: float, ring: list[list[float]]) -> bool:
    """Return whether a lon/lat point is inside a polygon ring."""
    inside = False
    j = len(ring) - 1
    for i, point in enumerate(ring):
        xi, yi = point[0], point[1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / (yj - yi) + xi
        ):
            inside = not inside
        j = i
    return inside


def point_in_polygon(lat: float, lon: float, rings: list[list[list[float]]]) -> bool:
    """Return whether a point is in an ArcGIS polygon, respecting holes."""
    containing = sum(1 for ring in rings if point_in_ring(lat, lon, ring))
    return containing % 2 == 1


def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = radians(lat1), radians(lat2)
    dl = radians(lon2 - lon1)
    return atan2(
        sin(dl) * cos(p2),
        cos(p1) * sin(p2) - sin(p1) * cos(p2) * cos(dl),
    )


def segment_distance_miles(
    lat: float,
    lon: float,
    a_lat: float,
    a_lon: float,
    b_lat: float,
    b_lon: float,
) -> float:
    """Approximate nearest great-circle distance to a segment."""
    segment = haversine_miles(a_lat, a_lon, b_lat, b_lon) / EARTH_RADIUS_MILES
    if segment == 0:
        return haversine_miles(lat, lon, a_lat, a_lon)
    start = haversine_miles(a_lat, a_lon, lat, lon) / EARTH_RADIUS_MILES
    bearing_delta = _bearing(a_lat, a_lon, lat, lon) - _bearing(
        a_lat, a_lon, b_lat, b_lon
    )
    cross_track = asin(max(-1.0, min(1.0, sin(start) * sin(bearing_delta))))
    along_track = atan2(sin(start) * cos(bearing_delta), cos(start))
    if along_track < 0:
        return haversine_miles(lat, lon, a_lat, a_lon)
    if along_track > segment:
        return haversine_miles(lat, lon, b_lat, b_lon)
    return abs(cross_track) * EARTH_RADIUS_MILES


def polygon_distance_miles(
    lat: float, lon: float, geometry: dict[str, Any]
) -> tuple[bool, float]:
    """Return containment and distance to nearest ArcGIS polygon edge."""
    rings = geometry.get("rings") or []
    if not rings:
        return False, float("inf")
    if point_in_polygon(lat, lon, rings):
        return True, 0.0
    distances = []
    for ring in rings:
        for first, second in pairwise(ring):
            distances.append(
                segment_distance_miles(
                    lat, lon, first[1], first[0], second[1], second[0]
                )
            )
    return False, min(distances, default=float("inf"))
