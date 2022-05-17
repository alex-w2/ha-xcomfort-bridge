from __future__ import annotations
from .hub import XComfortHub
from .windowshade import WindowShade
import logging

from homeassistant.components.cover import (
    CoverEntity,
    DEVICE_CLASS_SHADE,
    CoverEntityFeature
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import VERBOSE

_LOGGER = logging.getLogger(__name__)

def log(msg: str):
    if VERBOSE:
        _LOGGER.warning(msg)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    hub = XComfortHub.get_hub(hass, entry)

    devices = hub.devices

    _LOGGER.info(f"Found {len(devices)} xcomfort cover devices")

    sensors= list()
    for device in devices:
        if isinstance(device, WindowShade):
            _LOGGER.info(f"Adding {device}")
            sensors.append(XComfortWindowShade(device))

    _LOGGER.info(f"Added {len(sensors)} window shade units")
    async_add_entities(sensors)
    return

class XComfortWindowShade(CoverEntity):
    def __init__(self, device:WindowShade):
        self._device = device
        self._name = self._device.name
        self._attr_unique_id = f"shade_{self._device.name}_{self._device.device_id}"
        self._state = None

    async def async_added_to_hass(self):
        _LOGGER.warning(f"Added to hass {self._name} ")
        if self._device.state is None:
            _LOGGER.warning(f"State is null for {self._name}")
        else:
            self._device.state.subscribe(lambda state: self._state_change(state))

    def _state_change(self, state):
        self._state = state
        should_update = self._state is not None
        if should_update:
            self.async_write_ha_state()

    @property
    def device_class(self):
        return DEVICE_CLASS_SHADE

    @property
    def supported_features(self):
        return CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE\
         | CoverEntityFeature.SET_POSITION | CoverEntityFeature.STOP

    @property
    def current_cover_position(self):
        return self._state.current_cover_position

    @property
    def current_cover_tilt_position(self):
        return self._state.current_cover_tilt_position

    @property
    def is_opening(self):
        return None

    @property
    def is_closing(self):
        return None

    @property
    def is_closed(self):
        return None