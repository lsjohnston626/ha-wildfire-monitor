"""Wildfire Monitor integration."""

from __future__ import annotations

import asyncio

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NifcClient, NwsClient
from .const import PLATFORMS
from .coordinator import NifcCoordinator, NwsCoordinator, WildfireConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: WildfireConfigEntry) -> bool:
    """Set up one monitored location."""
    session = async_get_clientsession(hass)
    nifc = NifcCoordinator(hass, entry, NifcClient(session))
    nws = NwsCoordinator(hass, entry, NwsClient(session))

    results = await asyncio.gather(
        nifc.async_config_entry_first_refresh(),
        nws.async_config_entry_first_refresh(),
        return_exceptions=True,
    )
    if all(isinstance(result, Exception) for result in results):
        raise ConfigEntryNotReady("Both NIFC and NWS are unavailable")

    entry.runtime_data = (nifc, nws)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WildfireConfigEntry) -> bool:
    """Unload an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_entry(hass: HomeAssistant, entry: WildfireConfigEntry) -> None:
    """Reload after options change."""
    if entry.state is ConfigEntryState.LOADED:
        await hass.config_entries.async_reload(entry.entry_id)
