"""Event entity for Wildfire Monitor transitions."""

from __future__ import annotations

from typing import ClassVar

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import EVENT_TYPES
from .coordinator import WildfireConfigEntry
from .entity import wildfire_device_info
from .event_processor import MonitorEvent, WildfireEventDetector


class WildfireMonitorEventEntity(EventEntity):
    """Publish meaningful wildfire and alert transitions."""

    _attr_has_entity_name = True
    _attr_translation_key = "wildfire_events"
    _attr_icon = "mdi:alert-circle-outline"
    _attr_event_types: ClassVar[list[str]] = list(EVENT_TYPES)

    def __init__(self, entry, nifc, nws) -> None:
        self.entry = entry
        self.nifc = nifc
        self.nws = nws
        self._attr_unique_id = f"{entry.entry_id}_wildfire_events"
        self._attr_device_info = wildfire_device_info(entry)
        self._last_nifc_success = nifc.last_success
        self._last_nws_success = nws.last_success
        self._detector = WildfireEventDetector(
            nifc.data.records if nifc.data else [],
            nws.active_alerts,
            nifc_fresh=nifc.is_fresh,
            nws_fresh=nws.is_fresh,
            nifc_initialized=nifc.last_success is not None,
            nws_initialized=nws.last_success is not None,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe after the initial coordinator refreshes."""
        await super().async_added_to_hass()
        self.async_on_remove(self.nifc.async_add_listener(self._handle_nifc_update))
        self.async_on_remove(self.nws.async_add_listener(self._handle_nws_update))

    @callback
    def _handle_nifc_update(self) -> None:
        last_success = self.nifc.last_success
        successful_refresh = (
            last_success is not None and last_success != self._last_nifc_success
        )
        if successful_refresh:
            self._last_nifc_success = last_success
        self._emit(
            self._detector.process_nifc(
                self.nifc.data.records if self.nifc.data else [],
                successful_refresh=successful_refresh,
                is_fresh=self.nifc.is_fresh,
            )
        )

    @callback
    def _handle_nws_update(self) -> None:
        last_success = self.nws.last_success
        successful_refresh = (
            last_success is not None and last_success != self._last_nws_success
        )
        if successful_refresh:
            self._last_nws_success = last_success
        self._emit(
            self._detector.process_nws(
                self.nws.active_alerts,
                successful_refresh=successful_refresh,
                is_fresh=self.nws.is_fresh,
            )
        )

    @callback
    def _emit(self, events: list[MonitorEvent]) -> None:
        for event in events:
            self._trigger_event(
                event.event_type,
                {"location_name": self.entry.title, **event.data},
            )
            self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WildfireConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the event entity."""
    nifc, nws = entry.runtime_data
    async_add_entities([WildfireMonitorEventEntity(entry, nifc, nws)])
