"""Separate source coordinators for Wildfire Monitor."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import NifcClient, NwsClient, WildfireApiError
from .const import (
    CONF_RADIUS,
    DOMAIN,
    NIFC_STALE_AFTER,
    NIFC_UPDATE_INTERVAL,
    NWS_STALE_AFTER,
    NWS_UPDATE_INTERVAL,
)
from .models import Alert, SourceData
from .rules import unexpired

_LOGGER = logging.getLogger(__name__)


class SourceCoordinator(DataUpdateCoordinator[SourceData]):
    """Coordinator with explicit successful-refresh metadata."""

    stale_after = NIFC_STALE_AFTER

    @property
    def last_success(self) -> datetime | None:
        return self.data.last_success if self.data else None

    @property
    def is_fresh(self) -> bool:
        return bool(
            self.last_success
            and dt_util.utcnow() - self.last_success <= self.stale_after
        )


class NifcCoordinator(SourceCoordinator):
    """NIFC coordinator."""

    stale_after = NIFC_STALE_AFTER

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: NifcClient
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN} NIFC {entry.entry_id}",
            update_interval=NIFC_UPDATE_INTERVAL,
        )
        self.entry = entry
        self.client = client

    async def _async_update_data(self) -> SourceData:
        values = {**self.entry.data, **self.entry.options}
        try:
            records = await self.client.async_get_fires(
                values["latitude"], values["longitude"], values[CONF_RADIUS]
            )
        except WildfireApiError as err:
            raise UpdateFailed(f"NIFC update failed: {err}") from err
        return SourceData(records=records, last_success=dt_util.utcnow())


class NwsCoordinator(SourceCoordinator):
    """NWS coordinator."""

    stale_after = NWS_STALE_AFTER

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: NwsClient
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN} NWS {entry.entry_id}",
            update_interval=NWS_UPDATE_INTERVAL,
        )
        self.entry = entry
        self.client = client

    @property
    def active_alerts(self) -> list[Alert]:
        records = self.data.records if self.data else []
        return unexpired(records, dt_util.utcnow())

    async def _async_update_data(self) -> SourceData:
        values = {**self.entry.data, **self.entry.options}
        try:
            records = await self.client.async_get_alerts(
                values["latitude"], values["longitude"]
            )
        except WildfireApiError as err:
            raise UpdateFailed(f"NWS update failed: {err}") from err
        return SourceData(records=records, last_success=dt_util.utcnow())


type WildfireConfigEntry = ConfigEntry[tuple[NifcCoordinator, NwsCoordinator]]
