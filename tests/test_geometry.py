"""Geometry behavior."""

from custom_components.wildfire_monitor.geometry import (
    haversine_miles,
    point_in_polygon,
    polygon_distance_miles,
)


def test_haversine_known_distance() -> None:
    """One degree of longitude at the equator is about 69 miles."""
    assert 69.0 < haversine_miles(0, 0, 0, 1) < 69.2


def test_polygon_containment_and_hole() -> None:
    """Odd-even rings respect an interior hole."""
    outer = [[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]
    hole = [[-0.2, -0.2], [0.2, -0.2], [0.2, 0.2], [-0.2, 0.2], [-0.2, -0.2]]
    assert point_in_polygon(0.5, 0.5, [outer, hole])
    assert not point_in_polygon(0, 0, [outer, hole])


def test_polygon_inside_distance_zero() -> None:
    geometry = {"rings": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]]}
    assert polygon_distance_miles(0, 0, geometry) == (True, 0.0)


def test_polygon_edge_distance() -> None:
    geometry = {"rings": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}
    inside, distance = polygon_distance_miles(0.5, 2, geometry)
    assert not inside
    assert 69.0 < distance < 69.2


def test_missing_geometry() -> None:
    inside, distance = polygon_distance_miles(0, 0, {})
    assert not inside
    assert distance == float("inf")
