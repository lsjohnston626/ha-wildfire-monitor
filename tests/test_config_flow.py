"""Home Assistant config-flow tests (run when HA test support is installed)."""

import importlib.util

import pytest

if importlib.util.find_spec("homeassistant") is None:
    pytest.skip("Home Assistant is not installed", allow_module_level=True)

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.data_entry_flow import FlowResultType

from custom_components.wildfire_monitor.const import CONF_RADIUS, DOMAIN


async def test_user_flow_defaults_and_create(hass) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Cabin",
            CONF_LATITUDE: 47.1,
            CONF_LONGITUDE: -120.2,
            CONF_RADIUS: 50,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Cabin"


async def test_duplicate_location_aborts(hass) -> None:
    data = {
        CONF_NAME: "Home",
        CONF_LATITUDE: 47.1,
        CONF_LONGITUDE: -120.2,
        CONF_RADIUS: 50,
    }
    first = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=data
    )
    assert first["type"] is FlowResultType.CREATE_ENTRY
    second = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=data
    )
    assert second["reason"] == "already_configured"


async def test_multiple_locations_allowed(hass) -> None:
    for latitude in (47.1, 47.2):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_NAME: str(latitude),
                CONF_LATITUDE: latitude,
                CONF_LONGITUDE: -120.2,
                CONF_RADIUS: 50,
            },
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
