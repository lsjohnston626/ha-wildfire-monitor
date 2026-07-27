"""Device automation triggers for Wildfire Monitor."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_EVENT_DATA,
    CONF_PLATFORM,
    CONF_TYPE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, EVENT_TYPES, EVENT_WILDFIRE_MONITOR

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(EVENT_TYPES),
    }
)


def _entry_id_for_device(hass: HomeAssistant, device_id: str) -> str | None:
    """Return the Wildfire Monitor config entry identifier for a device."""
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        return None
    return next(
        (identifier[1] for identifier in device.identifiers if identifier[0] == DOMAIN),
        None,
    )


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, str]]:
    """Return all transitions supported by a monitored-location device."""
    if _entry_id_for_device(hass, device_id) is None:
        return []
    return [
        {
            CONF_PLATFORM: "device",
            CONF_DOMAIN: DOMAIN,
            CONF_DEVICE_ID: device_id,
            CONF_TYPE: event_type,
        }
        for event_type in EVENT_TYPES
    ]


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a device trigger to the integration event bus event."""
    entry_id = _entry_id_for_device(hass, config[CONF_DEVICE_ID])
    if entry_id is None:
        raise vol.Invalid("Wildfire Monitor device not found")

    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            CONF_PLATFORM: "event",
            event_trigger.CONF_EVENT_TYPE: EVENT_WILDFIRE_MONITOR,
            CONF_EVENT_DATA: {
                "entry_id": entry_id,
                CONF_TYPE: config[CONF_TYPE],
            },
        }
    )
    return await event_trigger.async_attach_trigger(
        hass,
        event_config,
        action,
        trigger_info,
        platform_type="device",
    )
