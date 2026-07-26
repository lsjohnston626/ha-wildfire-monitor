"""Sensors for Wildfire Monitor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfArea,
    UnitOfLength,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ALERT_SEVERITIES,
    EVACUATION_LEVELS,
    EVACUATION_STATUSES,
    MAX_ATTRIBUTE_RECORDS,
    THREAT_LEVELS,
)
from .coordinator import WildfireConfigEntry
from .entity import WildfireEntity
from .rules import evacuation_level, evacuation_status, threat_level


@dataclass(frozen=True, kw_only=True)
class WildfireSensorDescription(SensorEntityDescription):
    value_fn: Callable[[WildfireSensor], Any]
    availability_fn: Callable[[WildfireSensor], bool] = lambda entity: True


def _nearest(entity: WildfireSensor):
    return min(entity.fires, key=lambda fire: fire.distance_miles, default=None)


def _highest_severity(entity: WildfireSensor) -> str:
    priority = {"extreme": 4, "severe": 3, "moderate": 2, "minor": 1}
    return max(
        (alert.severity.casefold() for alert in entity.alerts),
        key=lambda value: priority.get(value, 0),
        default="none",
    )


DESCRIPTIONS = (
    WildfireSensorDescription(
        key="wildfire_threat_level",
        translation_key="wildfire_threat_level",
        device_class=SensorDeviceClass.ENUM,
        options=THREAT_LEVELS,
        icon="mdi:shield-alert",
        value_fn=lambda entity: threat_level(
            entity.fires,
            entity.alerts,
            entity.nifc.is_fresh,
            entity.nws.is_fresh,
        ),
        availability_fn=lambda entity: (
            threat_level(
                entity.fires,
                entity.alerts,
                entity.nifc.is_fresh,
                entity.nws.is_fresh,
            )
            is not None
        ),
    ),
    WildfireSensorDescription(
        key="evacuation_level",
        translation_key="evacuation_level",
        device_class=SensorDeviceClass.ENUM,
        options=EVACUATION_LEVELS,
        icon="mdi:sign-direction",
        value_fn=lambda entity: evacuation_level(entity.alerts),
        availability_fn=lambda entity: (
            evacuation_level(entity.alerts) != "none" or entity.nws.is_fresh
        ),
    ),
    WildfireSensorDescription(
        key="evacuation_status",
        translation_key="evacuation_status",
        device_class=SensorDeviceClass.ENUM,
        options=EVACUATION_STATUSES,
        icon="mdi:exit-run",
        value_fn=lambda entity: evacuation_status(entity.alerts),
        availability_fn=lambda entity: (
            evacuation_status(entity.alerts) != "none" or entity.nws.is_fresh
        ),
    ),
    WildfireSensorDescription(
        key="nearby_wildfire_count",
        translation_key="nearby_wildfire_count",
        icon="mdi:counter",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda entity: len(entity.fires),
        availability_fn=lambda entity: entity.nifc.is_fresh,
    ),
    WildfireSensorDescription(
        key="nearest_wildfire_name",
        translation_key="nearest_wildfire_name",
        icon="mdi:fire",
        value_fn=lambda entity: nearest.name if (nearest := _nearest(entity)) else None,
        availability_fn=lambda entity: entity.nifc.is_fresh,
    ),
    WildfireSensorDescription(
        key="nearest_wildfire_distance",
        translation_key="nearest_wildfire_distance",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.MILES,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:map-marker-distance",
        suggested_display_precision=1,
        value_fn=lambda entity: (
            round(nearest.distance_miles, 2) if (nearest := _nearest(entity)) else None
        ),
        availability_fn=lambda entity: entity.nifc.is_fresh,
    ),
    WildfireSensorDescription(
        key="nearest_wildfire_size",
        translation_key="nearest_wildfire_size",
        native_unit_of_measurement=UnitOfArea.ACRES,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:image-filter-hdr",
        value_fn=lambda entity: (
            nearest.acres if (nearest := _nearest(entity)) else None
        ),
        availability_fn=lambda entity: entity.nifc.is_fresh,
    ),
    WildfireSensorDescription(
        key="nearest_wildfire_containment",
        translation_key="nearest_wildfire_containment",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:progress-check",
        value_fn=lambda entity: (
            nearest.containment if (nearest := _nearest(entity)) else None
        ),
        availability_fn=lambda entity: entity.nifc.is_fresh,
    ),
    WildfireSensorDescription(
        key="active_fire_alert_count",
        translation_key="active_fire_alert_count",
        icon="mdi:alert",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda entity: len(entity.alerts),
        availability_fn=lambda entity: bool(entity.alerts) or entity.nws.is_fresh,
    ),
    WildfireSensorDescription(
        key="highest_fire_alert_severity",
        translation_key="highest_fire_alert_severity",
        device_class=SensorDeviceClass.ENUM,
        options=ALERT_SEVERITIES,
        icon="mdi:alert-decagram",
        value_fn=_highest_severity,
        availability_fn=lambda entity: bool(entity.alerts) or entity.nws.is_fresh,
    ),
    WildfireSensorDescription(
        key="nifc_last_success",
        translation_key="nifc_last_success",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda entity: entity.nifc.last_success,
    ),
    WildfireSensorDescription(
        key="nws_last_success",
        translation_key="nws_last_success",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda entity: entity.nws.last_success,
    ),
)


class WildfireSensor(WildfireEntity, SensorEntity):
    entity_description: WildfireSensorDescription

    def __init__(self, entry, nifc, nws, description) -> None:
        super().__init__(entry, nifc, nws, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        return self.entity_description.value_fn(self)

    @property
    def available(self) -> bool:
        return self.entity_description.availability_fn(self)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key == "nearby_wildfire_count":
            return {
                "nearby_fires": [
                    fire.as_attribute() for fire in self.fires[:MAX_ATTRIBUTE_RECORDS]
                ]
            }
        if self.entity_description.key == "active_fire_alert_count":
            return {
                "active_alerts": [
                    alert.as_attribute()
                    for alert in self.alerts[:MAX_ATTRIBUTE_RECORDS]
                ]
            }
        if self.entity_description.key in {
            "evacuation_level",
            "evacuation_status",
        }:
            source = next(
                (
                    alert.as_attribute()
                    for alert in self.alerts
                    if evacuation_level([alert]) != "none"
                    or evacuation_status([alert]) != "none"
                ),
                None,
            )
            return {"source_alert": source} if source else None
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WildfireConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    nifc, nws = entry.runtime_data
    async_add_entities(
        WildfireSensor(entry, nifc, nws, description) for description in DESCRIPTIONS
    )
