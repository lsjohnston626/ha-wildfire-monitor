"""NIFC and NWS parsing behavior."""

from custom_components.wildfire_monitor.api import (
    join_perimeters,
    parse_incidents,
    parse_nws_alerts,
)


def _incident(category="WF", name="Test Fire", irwin="{ABC}", x=0.1, y=0):
    return {
        "attributes": {
            "IncidentTypeCategory": category,
            "IncidentName": name,
            "IrwinID": irwin,
            "DailyAcres": 123,
            "PercentContained": 40,
        },
        "geometry": {"x": x, "y": y},
    }


def test_parse_wildfire_and_complex() -> None:
    fires = parse_incidents(
        {"features": [_incident(), _incident("CX", "Complex", "{DEF}", 0.2)]},
        0,
        0,
        50,
    )
    assert [fire.name for fire in fires] == ["Test Fire", "Complex"]
    assert fires[0].acres == 123
    assert fires[0].containment == 40


def test_filter_prescribed_and_outside_radius() -> None:
    fires = parse_incidents(
        {"features": [_incident("RX"), _incident("WF", x=2)]}, 0, 0, 50
    )
    assert fires == []


def test_missing_fields_do_not_break_parser() -> None:
    payload = {
        "features": [
            {
                "properties": {
                    "attr_IncidentTypeCategory": "WF",
                    "attr_IncidentName": None,
                },
                "geometry": {"coordinates": [0, 0]},
            },
            {"attributes": {"IncidentTypeCategory": "WF"}, "geometry": {}},
        ]
    }
    fires = parse_incidents(payload, 0, 0, 5)
    assert len(fires) == 1
    assert fires[0].name == "Unnamed wildfire"


def test_irwin_join_and_containment() -> None:
    fires = parse_incidents({"features": [_incident()]}, 0, 0, 50)
    perimeter = {
        "features": [
            {
                "attributes": {
                    "attr_IrwinID": "abc",
                    "attr_IncidentTypeCategory": "WF",
                    "poly_GISAcres": 999,
                },
                "geometry": {"rings": [[[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]]]},
            }
        ]
    }
    result = join_perimeters(fires, perimeter, 0, 0, 50)
    assert len(result) == 1
    assert result[0].inside_perimeter
    assert result[0].distance_miles == 0


def test_perimeter_only_fire_and_prescribed_filter() -> None:
    payload = {
        "features": [
            {
                "attributes": {
                    "attr_IncidentTypeCategory": "WF",
                    "poly_IncidentName": "Perimeter Fire",
                },
                "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
            },
            {
                "attributes": {"attr_IncidentTypeCategory": "RX"},
                "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]},
            },
        ]
    }
    result = join_perimeters([], payload, 0.5, 0.5, 50)
    assert [fire.name for fire in result] == ["Perimeter Fire"]


def test_nws_parsing_filters_and_preserves_official_fields() -> None:
    payload = {
        "features": [
            {
                "id": "https://api.weather.gov/alerts/1",
                "properties": {
                    "event": "Red Flag Warning",
                    "headline": "Critical fire weather",
                    "description": "Official text",
                    "instruction": "Avoid sparks",
                    "expires": "2030-01-01T00:00:00Z",
                    "senderName": "NWS Spokane",
                    "severity": "Severe",
                    "urgency": "Expected",
                    "certainty": "Likely",
                },
            },
            {"id": "2", "properties": {"event": "Flood Warning"}},
        ]
    }
    alerts = parse_nws_alerts(payload)
    assert len(alerts) == 1
    assert alerts[0].sender == "NWS Spokane"
    assert alerts[0].instruction == "Avoid sparks"
    assert alerts[0].source_url == "https://api.weather.gov/alerts/1"
