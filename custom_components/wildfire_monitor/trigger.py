"""First-class automation triggers for Wildfire Monitor."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

import voluptuous as vol
from homeassistant.const import ATTR_ENTITY_ID, CONF_OPTIONS, CONF_TARGET
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.target import (
    TargetSelection,
    async_extract_referenced_entity_ids,
)
from homeassistant.helpers.trigger import (
    Trigger,
    TriggerActionRunner,
    TriggerConfig,
    TriggerNotTriggeredReporter,
)
from homeassistant.helpers.typing import ConfigType

from .const import EVENT_TYPES, EVENT_WILDFIRE_MONITOR

_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TARGET): cv.TARGET_FIELDS,
        vol.Required(CONF_OPTIONS, default={}): {},
    }
)


class WildfireTransitionTrigger(Trigger):
    """Trigger on one specific Wildfire Monitor transition."""

    event_type: str

    @classmethod
    @override
    async def async_validate_config(
        cls, hass: HomeAssistant, config: ConfigType
    ) -> ConfigType:
        """Validate trigger configuration."""
        return cast(ConfigType, _CONFIG_SCHEMA(config))

    def __init__(self, hass: HomeAssistant, config: TriggerConfig) -> None:
        """Initialize the trigger."""
        super().__init__(hass, config)
        if TYPE_CHECKING:
            assert config.target is not None
        self._target = config.target

    @override
    async def async_attach_runner(
        self,
        run_action: TriggerActionRunner,
        did_not_trigger: TriggerNotTriggeredReporter | None = None,
    ) -> CALLBACK_TYPE:
        """Listen for this transition on the selected locations."""
        target_selection = TargetSelection(self._target)
        if not target_selection.has_any_target:
            raise HomeAssistantError(f"No target defined in {self._target}")

        selected = async_extract_referenced_entity_ids(
            self._hass,
            target_selection,
            primary_entities_only=False,
        )
        entity_ids = selected.referenced | selected.indirectly_referenced

        @callback
        def handle_event(event: Event) -> None:
            if (
                event.data.get("type") != self.event_type
                or event.data.get(ATTR_ENTITY_ID) not in entity_ids
            ):
                return
            run_action(
                dict(event.data),
                description=f"Wildfire Monitor {self.event_type} trigger",
            )

        return self._hass.bus.async_listen(EVENT_WILDFIRE_MONITOR, handle_event)


def _make_trigger(event_type: str) -> type[WildfireTransitionTrigger]:
    """Create a trigger class bound to one transition type."""
    return type(
        f"{event_type.title().replace('_', '')}Trigger",
        (WildfireTransitionTrigger,),
        {"event_type": event_type},
    )


TRIGGERS: dict[str, type[Trigger]] = {
    event_type: _make_trigger(event_type) for event_type in EVENT_TYPES
}


async def async_get_triggers(hass: HomeAssistant) -> dict[str, type[Trigger]]:
    """Return Wildfire Monitor's first-class automation triggers."""
    return TRIGGERS
