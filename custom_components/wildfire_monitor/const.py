"""Constants for Wildfire Monitor."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "wildfire_monitor"
PLATFORMS: Final = ["binary_sensor", "sensor"]

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
USER_AGENT: Final = "WildfireMonitor/0.1.0 (Home Assistant custom integration)"

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
