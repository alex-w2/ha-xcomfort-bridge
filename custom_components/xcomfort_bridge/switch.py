import logging
from typing import Optional

from xcomfort.devices import Rocker

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, VERBOSE
from .hub import XComfortHub
import re

_LOGGER = logging.getLogger(__name__)


def log(msg: str):
    if VERBOSE:
        _LOGGER.info(msg)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    hub = XComfortHub.get_hub(hass, entry)

    switches = list()
    for device in hub.devices:
        if isinstance(device, Rocker):
            _LOGGER.info(f"Adding {device}")
            switch = XComfortSwitch(hass, hub, device)
            switches.append(switch)

    async_add_entities(switches)


class XComfortSwitch(SwitchEntity):
    def __init__(self, hass: HomeAssistant, hub: XComfortHub, device: Rocker):
        self.hass = hass
        self.hub = hub

        self._attr_device_class = SwitchDeviceClass.SWITCH
        self._device = device
        self._name = device.name
        self._state = None
        self.device_id = device.device_id

        # Workaround for XComfort rockets switches being named just
        # "Rocker 1" etc, prefix with component name when possible
        comp_name = hub.get_component_name(device.comp_id)
        if comp_name is not None:
            self._name = f"{comp_name} - {self._name}"

        self._unique_id = f"switch_{DOMAIN}_{hub.identifier}-{device.device_id}"
        self.event_name = self.generate_event_name()

    def generate_event_name(self):
        # Unique ID isn't very suitable for the event name, as it is hard for the user
        #  to figure out what it would be. Instead, use device name and remove some
        #  special characters. e.g. switch_xcomfort_bridge_hallway_rocker_1
        event_name = re.sub(r'_+', '_', f"switch_{DOMAIN}_{re.sub(r'[ /\-.]', '_', self._name.lower())}")
        _LOGGER.info(f"Enabled event: '{event_name}' for {self._name}")
        return event_name

    async def async_added_to_hass(self) -> None:
        self._device.state.subscribe(self._state_change)

    def _state_change(self, state) -> None:
        self._state = state
        should_update = self._state is not None

        if should_update:
            self.schedule_update_ha_state()
            # Emit event to enable stateless automation, since
            # actual switch state may be same as before
            self.hass.bus.fire(self.event_name, {"on": state})

    @property
    def is_on(self) -> Optional[bool]:
        return self._state

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID."""
        return self._unique_id

    @property
    def should_poll(self) -> bool:
        return False

    async def async_turn_on(self, **kwargs):
        pass

    async def async_turn_off(self, **kwargs):
        pass
