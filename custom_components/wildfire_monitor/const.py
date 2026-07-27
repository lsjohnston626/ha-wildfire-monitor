"""Constants for Wildfire Monitor."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "wildfire_monitor"
DOCUMENTATION_URL: Final = "https://github.com/lsjohnston626/ha-wildfire-monitor#readme"
PLATFORMS: Final = ["binary_sensor", "event", "sensor"]

CONF_RADIUS: Final = "radius"
DEFAULT_NAME: Final = "Wildfire Monitor"
DEFAULT_RADIUS: Final = 50.0
MIN_RADIUS: Final = 5.0
MAX_RADIUS: Final = 250.0

NIFC_UPDATE_INTERVAL: Final = timedelta(minutes=10)
NWS_UPDATE_INTERVAL: Final = timedelta(minutes=5)
NIFC_STALE_AFTER: Final = timedelta(minutes=30)
NWS_STALE_AFTER: Final = timedelta(minutes=15)
MAX_ATTRIBUTE_RECORDS: Final = 20

NIFC_INCIDENT_URL: Final = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "WFIGS_Incident_Locations_Current/FeatureServer/0/query"
)
NIFC_PERIMETER_URL: Final = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "WFIGS_Interagency_Perimeters_Current/FeatureServer/0/query"
)
NWS_ALERTS_URL: Final = "https://api.weather.gov/alerts/active"
USER_AGENT: Final = "WildfireMonitor/0.2.1 (Home Assistant custom integration)"
EVENT_WILDFIRE_MONITOR: Final = f"{DOMAIN}_event"

EVENT_WILDFIRE_DISCOVERED: Final = "wildfire_discovered"
EVENT_WILDFIRE_NO_LONGER_NEARBY: Final = "wildfire_no_longer_nearby"
EVENT_FIRE_ENTERED_PERIMETER: Final = "fire_entered_perimeter"
EVENT_OFFICIAL_ALERT_STARTED: Final = "official_alert_started"
EVENT_OFFICIAL_ALERT_ENDED: Final = "official_alert_ended"
EVENT_THREAT_LEVEL_INCREASED: Final = "threat_level_increased"
EVENT_THREAT_LEVEL_DECREASED: Final = "threat_level_decreased"
EVENT_EVACUATION_LEVEL_INCREASED: Final = "evacuation_level_increased"
EVENT_EVACUATION_LEVEL_DECREASED: Final = "evacuation_level_decreased"
EVENT_SOURCE_STALE: Final = "source_stale"
EVENT_SOURCE_RECOVERED: Final = "source_recovered"
EVENT_TYPES: Final = (
    EVENT_WILDFIRE_DISCOVERED,
    EVENT_WILDFIRE_NO_LONGER_NEARBY,
    EVENT_FIRE_ENTERED_PERIMETER,
    EVENT_OFFICIAL_ALERT_STARTED,
    EVENT_OFFICIAL_ALERT_ENDED,
    EVENT_THREAT_LEVEL_INCREASED,
    EVENT_THREAT_LEVEL_DECREASED,
    EVENT_EVACUATION_LEVEL_INCREASED,
    EVENT_EVACUATION_LEVEL_DECREASED,
    EVENT_SOURCE_STALE,
    EVENT_SOURCE_RECOVERED,
)

EVACUATION_LEVELS: Final = [
    "none",
    "unclassified",
    "level_1_ready",
    "level_2_set",
    "level_3_go",
]
EVACUATION_STATUSES: Final = [
    "none",
    "advisory",
    "warning",
    "order",
    "immediate",
    "unknown",
]
THREAT_LEVELS: Final = ["none", "low", "moderate", "high", "extreme"]
ALERT_SEVERITIES: Final = ["none", "unknown", "minor", "moderate", "severe", "extreme"]
