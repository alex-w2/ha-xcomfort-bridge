import logging

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, VERBOSE
from .hub import XComfortHub, Switch

_LOGGER = logging.getLogger(__name__)


def log(msg: str):
    if VERBOSE:
        _LOGGER.info(msg)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    hub = XComfortHub.get_hub(hass, entry)

    devices = hub.devices

    _LOGGER.info(f"Found {len(devices)} xcomfort devices")

    switches = list()
    for device in devices:
        if isinstance(device, Switch):
            _LOGGER.info(f"Adding {device}")
            switch = HASSXComfortSwitch(hass, hub, device)
            switches.append(switch)

    _LOGGER.info(f"Added {len(switches)} switches")
    async_add_entities(switches)


class HASSXComfortSwitch(SwitchEntity):
    def __init__(self, hass: HomeAssistant, hub: XComfortHub, device: Switch):
        self.hass = hass
        self.hub = hub

        self._attr_device_class =  SwitchDeviceClass.SWITCH
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

    async def async_added_to_hass(self):
        log(f"Added to hass {self._name} ")
        if self._device.state is None:
            log(f"State is null for {self._name}")
        else:
            self._device.state.subscribe(lambda state: self._state_change(state))

    def _state_change(self, state):
        self._state = state

        should_update = self._state is not None

        log(f"State changed {self._name} : {state}")

        if should_update:
            self.schedule_update_ha_state()
            # Emit event to enable stateless automation, since
            # actual switch state may be same as before
            log(f"Event 'xcomfort_rocker_{self._name}' : {state.on}")
            self.hub.bridge.bus.fire(f"xcomfort_rocker_{self._name}", {"on": state.on })

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Eaton",
            "model": "XXX",
            "sw_version": "Unknown",
            "via_device": self.hub.hub_id,
        }

    @property
    def is_on(self):
        return self._state.on

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self._unique_id

    @property
    def should_poll(self) -> bool:
        return False

    async def async_turn_on(self, **kwargs):
        await self._device.turn_on()

    async def async_turn_off(self, **kwargs):
        await self._device.turn_off()
