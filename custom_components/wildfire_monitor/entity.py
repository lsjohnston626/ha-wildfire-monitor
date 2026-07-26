"""Shared entity support for Wildfire Monitor."""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOCUMENTATION_URL, DOMAIN
from .coordinator import NifcCoordinator, NwsCoordinator, WildfireConfigEntry


class WildfireEntity(CoordinatorEntity[NifcCoordinator]):
    """Entity that listens to both independent source coordinators."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: WildfireConfigEntry,
        nifc: NifcCoordinator,
        nws: NwsCoordinator,
        key: str,
    ) -> None:
        super().__init__(nifc)
        self.entry = entry
        self.nifc = nifc
        self.nws = nws
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Wildfire Monitor",
            model="Official NIFC and NWS data",
            configuration_url=DOCUMENTATION_URL,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to both coordinators."""
        await super().async_added_to_hass()
        self.async_on_remove(self.nws.async_add_listener(self._handle_nws_update))

    @callback
    def _handle_nws_update(self) -> None:
        self.async_write_ha_state()

    @property
    def fires(self):
        """Return fires only while NIFC data is fresh."""
        return self.nifc.data.records if self.nifc.data and self.nifc.is_fresh else []

    @property
    def alerts(self):
        """Return unexpired cached official alerts."""
        return self.nws.active_alerts
