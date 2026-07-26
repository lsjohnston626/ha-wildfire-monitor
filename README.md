# Wildfire Monitor

<p align="center">
  <img src="custom_components/wildfire_monitor/brand/icon.png"
       alt="Wildfire Monitor icon"
       width="180">
</p>

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Home Assistant 2025.1+](https://img.shields.io/badge/Home%20Assistant-2025.1%2B-41BDF5.svg)](https://www.home-assistant.io/)
[![Validate](https://github.com/lsjohnston626/ha-wildfire-monitor/actions/workflows/validate.yml/badge.svg)](https://github.com/lsjohnston626/ha-wildfire-monitor/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Wildfire Monitor is a custom integration for Home Assistant that watches a
named location for nearby wildfires, reported fire perimeters, official fire
weather alerts, and evacuation information.

It uses keyless data from
[NIFC WFIGS](https://data-nifc.opendata.arcgis.com/) and the
[National Weather Service API](https://www.weather.gov/documentation/services-web-api).
Multiple locations can be monitored with separate config entries.

> [!CAUTION]
> Wildfire Monitor is an awareness aid, not an emergency notification system.
> Official data can be delayed, incomplete, revised, or unavailable. Never
> delay evacuation or other protective action based on this integration.
> Follow instructions from local emergency management and public-safety
> officials.

## Features

- Monitors wildfires within a configurable 5-250 mile radius.
- Uses incident points and reported perimeters to calculate distance.
- Detects when the configured point is inside a reported fire perimeter.
- Retrieves official NWS alerts for the exact configured coordinates.
- Conservatively maps official alert language to Ready/Set/Go evacuation
  levels without inferring evacuation from fire proximity.
- Keeps NIFC and NWS operational independently during a partial outage.
- Prevents stale or missing data from producing reassuring negative states.
- Exposes source availability and last-success diagnostic entities.
- Uses Home Assistant's shared HTTP session with no API keys or additional
  runtime dependencies.

## Requirements

- Home Assistant 2025.1 or newer
- HACS for the recommended installation method
- Internet access to the public NIFC ArcGIS and NWS API endpoints

The data sources primarily cover the United States. Availability and detail
vary by incident and issuing authority.

## Installation

### HACS

[![Open your Home Assistant instance and add this repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=lsjohnston626&repository=ha-wildfire-monitor&category=integration)

1. Open the button above, or add
   `https://github.com/lsjohnston626/ha-wildfire-monitor` to HACS as a custom
   **Integration** repository.
2. Install **Wildfire Monitor**.
3. Restart Home Assistant.
4. Go to **Settings > Devices & services > Add integration** and select
   **Wildfire Monitor**.

HACS installs the files but does not configure a monitored location. Complete
the final step in Home Assistant after the restart.

### Manual

1. Copy `custom_components/wildfire_monitor` from this repository to
   `/config/custom_components/wildfire_monitor` in Home Assistant.
2. Restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration** and select
   **Wildfire Monitor**.

## Configuration

Each config entry represents one monitored location. The form starts with
Home Assistant's configured coordinates.

| Option | Default | Allowed values | Description |
|---|---:|---:|---|
| Name | Wildfire Monitor | Text | Identifies the location and its device |
| Latitude | Home Assistant latitude | -90 to 90 | Monitored point |
| Longitude | Home Assistant longitude | -180 to 180 | Monitored point |
| Radius | 50 miles | 5-250 miles | NIFC wildfire search distance |

Add another config entry to monitor another location. Home Assistant prevents
the same rounded coordinates from being configured twice. Use
**Settings > Devices & services > Wildfire Monitor > Configure** to edit an
existing entry; changes reload that entry automatically.

## Entities

Home Assistant includes the location name in generated entity IDs when needed,
especially when more than one location is configured.

### Binary sensors

| Entity suffix | On when |
|---|---|
| `binary_sensor.wildfire_nearby` | At least one wildfire is within the configured radius |
| `binary_sensor.wildfire_inside_perimeter` | The location is inside a reported fire perimeter |
| `binary_sensor.fire_weather_alert` | A Red Flag Warning, Fire Weather Watch, or Extreme Fire Danger alert is active |
| `binary_sensor.fire_warning` | An NWS Fire Warning is active |
| `binary_sensor.evacuation_alert` | An official alert contains evacuation context |

### Sensors

| Entity suffix | State or measurement |
|---|---|
| `sensor.wildfire_threat_level` | `none`, `low`, `moderate`, `high`, or `extreme` |
| `sensor.evacuation_level` | `none`, `unclassified`, `level_1_ready`, `level_2_set`, or `level_3_go` |
| `sensor.evacuation_status` | `none`, `advisory`, `warning`, `order`, `immediate`, or `unknown` |
| `sensor.nearby_wildfire_count` | Number of wildfires within the configured radius |
| `sensor.nearest_wildfire_name` | Name of the nearest wildfire |
| `sensor.nearest_wildfire_distance` | Great-circle or nearest-perimeter-edge distance |
| `sensor.nearest_wildfire_size` | Reported incident size in acres |
| `sensor.nearest_wildfire_containment` | Reported containment percentage |
| `sensor.active_fire_alert_count` | Number of active fire-related NWS alerts |
| `sensor.highest_fire_alert_severity` | Highest reported NWS severity |

The wildfire count sensor exposes up to 20 distance-sorted records in its
`nearby_fires` attribute. The alert count sensor exposes up to 20
urgency-sorted official records in `active_alerts`. Polygon geometry is never
stored in entity attributes.

### Diagnostics

These entities are disabled by default and can be enabled from the Wildfire
Monitor device page:

| Entity suffix | Description |
|---|---|
| `binary_sensor.nifc_source_available` | NIFC data is currently fresh |
| `binary_sensor.nws_source_available` | NWS data is currently fresh |
| `sensor.nifc_last_success` | Last successful NIFC update |
| `sensor.nws_last_success` | Last successful NWS update |

## Evacuation classification

Evacuation levels are derived only from official NWS alert content. Fire
distance by itself never creates an evacuation level.

| Official alert language | Evacuation level |
|---|---|
| Explicit Level 1 or evacuation-context "Be Ready" | `level_1_ready` |
| Explicit Level 2 or evacuation-context "Be Set" | `level_2_set` |
| Explicit Level 3, "Go Now", "leave immediately", evacuation order, or `Evacuation Immediate` | `level_3_go` |
| Evacuation-related language without a reliable mapping | `unclassified` |
| No evacuation-related alert | `none` |

When conflicting phrases occur, the highest reliably detected level wins.
The separate evacuation status sensor preserves broader source terminology:
`advisory`, `warning`, `order`, `immediate`, or `unknown`.

NWS does not provide uniformly structured Level 1/2/3 evacuation zones
nationwide. Classification is intentionally conservative, and the source
alert is retained in entity attributes.

## Threat classification

| Threat | Conditions |
|---|---|
| `extreme` | Inside a fire perimeter, Level 3, evacuation order, or evacuation immediate |
| `high` | Fire within 5 miles, Level 2, or NWS Fire Warning |
| `moderate` | Fire within 15 miles, Level 1, evacuation warning, Red Flag Warning, Extreme Fire Danger, or Fire Weather Watch |
| `low` | Another wildfire exists within the configured radius |
| `none` | Both sources are fresh and no condition above applies |

Containment and acreage are informational and never lower the threat level.

## Updates and availability

| Source | Update interval | Considered stale after |
|---|---:|---:|
| NWS alerts | 5 minutes | 15 minutes |
| NIFC incidents and perimeters | 10 minutes | 30 minutes |

The source coordinators operate independently. A transient failure retains the
last successful response, but stale data cannot produce a reassuring
`none`/off state. Unexpired positive NWS alerts can remain visible from cache;
expired alerts are removed.

## Data handling and limitations

- NWS receives the configured latitude and longitude.
- NIFC's ArcGIS services receive the coordinates and search radius.
- No API key, Home Assistant credential, or personal identifier is sent.
- Incident locations, acreage, containment, and perimeter geometry may lag
  real-world conditions.
- Not every incident has a perimeter or complete incident metadata.
- Point containment and nearest-edge distance depend on the latest reported
  perimeter and do not predict fire spread.
- Local authorities may issue evacuation information outside NWS or use
  terminology that cannot be classified reliably.

## Troubleshooting

1. Enable the four diagnostic entities and check source freshness and
   last-success timestamps.
2. Confirm that the configured coordinates and radius are correct.
3. Confirm Home Assistant can reach `api.weather.gov` and
   `services3.arcgis.com`.
4. Restart Home Assistant after a manual installation or upgrade.

For additional logging:

```yaml
logger:
  logs:
    custom_components.wildfire_monitor: debug
```

When reporting a problem, include:

- Home Assistant and Wildfire Monitor versions
- Which source diagnostic is unavailable
- Relevant logs with private location details removed
- Expected and actual entity states

Report issues at
[github.com/lsjohnston626/ha-wildfire-monitor/issues](https://github.com/lsjohnston626/ha-wildfire-monitor/issues).

## Removal

1. Remove every Wildfire Monitor config entry from
   **Settings > Devices & services**.
2. Uninstall the repository from HACS, or remove
   `/config/custom_components/wildfire_monitor` after a manual installation.
3. Restart Home Assistant.

## Development

Create a virtual environment, install the test requirements, and run:

```text
python -m pip install -r requirements_test.txt
python -m pytest
python -m ruff check .
python -m ruff format --check .
```

Pull requests should include tests for behavior changes and keep the
integration free of additional runtime dependencies unless clearly justified.

## License

Wildfire Monitor is released under the [MIT License](LICENSE).
