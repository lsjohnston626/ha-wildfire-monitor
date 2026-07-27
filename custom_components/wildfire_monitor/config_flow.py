"""Config and options flows for Wildfire Monitor."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_RADIUS,
    DEFAULT_NAME,
    DEFAULT_RADIUS,
    DOMAIN,
    MAX_RADIUS,
    MIN_RADIUS,
)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)
            ): selector.TextSelector(),
            vol.Required(
                CONF_LATITUDE, default=defaults.get(CONF_LATITUDE)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-90, max=90, step="any")
            ),
            vol.Required(
                CONF_LONGITUDE, default=defaults.get(CONF_LONGITUDE)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-180, max=180, step="any")
            ),
            vol.Required(
                CONF_RADIUS, default=defaults.get(CONF_RADIUS, DEFAULT_RADIUS)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_RADIUS,
                    max=MAX_RADIUS,
                    step=1,
                    unit_of_measurement="mi",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )


def _location_unique_id(latitude: Any, longitude: Any) -> str:
    """Return the stable identity used to prevent duplicate locations."""
    return f"{float(latitude):.5f},{float(longitude):.5f}"


class WildfireMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a monitored location."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            await self.async_set_unique_id(
                _location_unique_id(
                    user_input[CONF_LATITUDE], user_input[CONF_LONGITUDE]
                )
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=_schema(
                {
                    CONF_LATITUDE: self.hass.config.latitude,
                    CONF_LONGITUDE: self.hass.config.longitude,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return WildfireMonitorOptionsFlow()


class WildfireMonitorOptionsFlow(config_entries.OptionsFlow):
    """Edit a monitored location."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            unique_id = _location_unique_id(
                user_input[CONF_LATITUDE], user_input[CONF_LONGITUDE]
            )
            for other in self.hass.config_entries.async_entries(DOMAIN):
                if (
                    other.entry_id != self.config_entry.entry_id
                    and other.unique_id == unique_id
                ):
                    errors["base"] = "already_configured"
                    break
            if not errors:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=user_input[CONF_NAME],
                    unique_id=unique_id,
                )
                return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=_schema(
                {**self.config_entry.data, **self.config_entry.options}
            ),
            errors=errors,
        )
