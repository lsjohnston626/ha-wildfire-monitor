"""Binary sensors for Wildfire Monitor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import WildfireConfigEntry
from .entity import WildfireEntity
from .rules import is_evacuation_alert


@dataclass(frozen=True, kw_only=True)
class WildfireBinaryDescription(BinarySensorEntityDescription):
    """Wildfire binary sensor description."""

    value_fn: Callable[[WildfireBinarySensor], bool | None]


def _nifc_value(entity: WildfireBinarySensor, predicate) -> bool | None:
    if not entity.nifc.is_fresh:
        return None
    return any(predicate(fire) for fire in entity.fires)


def _nws_value(entity: WildfireBinarySensor, predicate) -> bool | None:
    if any(predicate(alert) for alert in entity.alerts):
        return True
    return False if entity.nws.is_fresh else None


DESCRIPTIONS = (
    WildfireBinaryDescription(
        key="wildfire_nearby",
        translation_key="wildfire_nearby",
        icon="mdi:fire",
        value_fn=lambda entity: _nifc_value(entity, lambda fire: True),
    ),
    WildfireBinaryDescription(
        key="wildfire_inside_perimeter",
        translation_key="wildfire_inside_perimeter",
        icon="mdi:map-marker-alert",
        value_fn=lambda entity: _nifc_value(entity, lambda fire: fire.inside_perimeter),
    ),
    WildfireBinaryDescription(
        key="fire_weather_alert",
        translation_key="fire_weather_alert",
        icon="mdi:weather-windy",
        value_fn=lambda entity: _nws_value(
            entity,
            lambda alert: (
                alert.event
                in {"Red Flag Warning", "Fire Weather Watch", "Extreme Fire Danger"}
            ),
        ),
    ),
    WildfireBinaryDescription(
        key="fire_warning",
        translation_key="fire_warning",
        icon="mdi:alert-octagon",
        value_fn=lambda entity: _nws_value(
            entity, lambda alert: alert.event == "Fire Warning"
        ),
    ),
    WildfireBinaryDescription(
        key="evacuation_alert",
        translation_key="evacuation_alert",
        icon="mdi:run-fast",
        value_fn=lambda entity: _nws_value(entity, is_evacuation_alert),
    ),
    WildfireBinaryDescription(
        key="nifc_source_available",
        translation_key="nifc_source_available",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:database-check",
        value_fn=lambda entity: entity.nifc.is_fresh,
    ),
    WildfireBinaryDescription(
        key="nws_source_available",
        translation_key="nws_source_available",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        icon="mdi:database-check",
        value_fn=lambda entity: entity.nws.is_fresh,
    ),
)


class WildfireBinarySensor(WildfireEntity, BinarySensorEntity):
    """A combined-source binary sensor."""

    entity_description: WildfireBinaryDescription

    def __init__(self, entry, nifc, nws, description) -> None:
        super().__init__(entry, nifc, nws, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self)

    @property
    def available(self) -> bool:
        return self.is_on is not None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WildfireConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    nifc, nws = entry.runtime_data
    async_add_entities(
        WildfireBinarySensor(entry, nifc, nws, description)
        for description in DESCRIPTIONS
    )
