"""Support for mill wifi-enabled home heaters."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from xcomfort.bridge import Room

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    POWER_WATT,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, VERBOSE

from .hub import XComfortHub

_LOGGER = logging.getLogger(__name__)

def log(msg: str):
    if VERBOSE:
        _LOGGER.info(msg)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    hub = XComfortHub.get_hub(hass, entry)

    rooms = hub.rooms
    devices = hub.devices

    _LOGGER.info(f"Found {len(rooms)} xcomfort rooms")
    _LOGGER.info(f"Found {len(devices)} xcomfort devices")

    sensors = list()
    for room in rooms:
        if room.state.value is not None:
            if room.state.value.power is not None:
                _LOGGER.info(f"Adding power sensor for room {room.name}")
                sensors.append(XComfortPowerSensor(room))

            if room.state.value.humidity is not None:
                _LOGGER.info(f"Adding humidity sensor for room {room.name}")
                sensors.append(XComfortHumiditySensor(room))

            if room.state.value.temperature is not None:
                _LOGGER.info(f"Adding temperature sensor for room {room.name}")
                sensors.append(XComfortTemperatureSensor(room))

    _LOGGER.info(f"Added {len(sensors)} rc touch units")
    async_add_entities(sensors)
    return


class XComfortPowerSensor(SensorEntity):
    def __init__(self, room: Room):
        self._attr_device_class = SensorEntityDescription(
            key="current_consumption",
            device_class=SensorDeviceClass.ENERGY,
            native_unit_of_measurement=POWER_WATT,
            state_class=SensorStateClass.MEASUREMENT,
            name="Current consumption",
        )
        self._room = room
        self._attr_name = self._room.name
        self._attr_name = f"{self._room.name} Energy"
        self._attr_unique_id = f"energy_{self._room.room_id}"
        self._state = None

    async def async_added_to_hass(self):
        _LOGGER.info(f"Added to hass {self._attr_name} ")
        if self._room.state is None:
            _LOGGER.warning(f"State is null for {self._attr_name}")
        else:
            self._room.state.subscribe(lambda state: self._state_change(state))

    def _state_change(self, state):
        self._state = state
        should_update = self._state is not None
        if should_update:
            self.async_write_ha_state()

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

    @property
    def native_unit_of_measurement(self):
        return POWER_WATT

    @property
    def native_value(self):
        return self._state.power

class XComfortHumiditySensor(SensorEntity):
    def __init__(self, room:Room):
        self._attr_device_class = SensorEntityDescription(
            key="humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            name="Humidity",)
        self._room = room
        self._attr_name = f"{self._room.name} Humidity"
        self._attr_unique_id = f"humidity_{self._room.room_id}"
        self._state = None

    async def async_added_to_hass(self):
        _LOGGER.info(f"Added to hass {self._attr_name} ")
        if self._room.state is None:
            _LOGGER.warning(f"State is null for {self._attr_name}")
        else:
            self._room.state.subscribe(lambda state: self._state_change(state))

    def _state_change(self, state):
        self._state = state
        should_update = self._state is not None
        log(f"State changed {self._attr_name} : {state}")
        if should_update:
            self.async_write_ha_state()

    @property
    def device_class(self):
        return SensorDeviceClass.HUMIDITY

    @property
    def native_unit_of_measurement(self):
        return PERCENTAGE

    @property
    def native_value(self):
        return self._state.humidity


class XComfortTemperatureSensor(SensorEntity):
    def __init__(self, room:Room):
        self._attr_device_class = SensorEntityDescription(
            key="temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=TEMP_CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            name="Temperature",)
        self._room = room
        self._attr_name = f"{self._room.name} Temperature"
        self._attr_unique_id = f"temperature_{self._room.room_id}"
        self._state = None

    async def async_added_to_hass(self):
        _LOGGER.info(f"Added to hass {self._attr_name} ")
        if self._room.state is None:
            _LOGGER.warning(f"State is null for {self._attr_name}")
        else:
            self._room.state.subscribe(lambda state: self._state_change(state))

    def _state_change(self, state):
        self._state = state
        should_update = self._state is not None
        log(f"State changed {self._attr_name} : {state}")
        if should_update:
            self.async_write_ha_state()

    @property
    def device_class(self):
        return SensorDeviceClass.TEMPERATURE

    @property
    def native_unit_of_measurement(self):
        return TEMP_CELSIUS

    @property
    def native_value(self):
        return self._state.temperature
