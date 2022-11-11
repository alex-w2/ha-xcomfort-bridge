"""Support for mill wifi-enabled home heaters."""
from __future__ import annotations
from .hub import XComfortHub
import time
import math
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from xcomfort.bridge import Bridge, Room
from xcomfort.devices import RcTouch

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ENERGY_KILO_WATT_HOUR,
    PERCENTAGE,
    POWER_WATT,
    TEMP_CELSIUS
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, VERBOSE

_LOGGER = logging.getLogger(__name__)

def log(msg: str):
    if VERBOSE:
        _LOGGER.warning(msg)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    hub = XComfortHub.get_hub(hass, entry)

    rooms = hub.rooms
    devices = hub.devices

    _LOGGER.info(f"Found {len(rooms)} xcomfort rooms")
    _LOGGER.info(f"Found {len(devices)} xcomfort devices")

    sensors= list()
    for room in rooms:
        if room.state.value.power is not None:
            _LOGGER.info(f"Adding power sensor for room {room.name}")
            sensors.append(XComfortPowerSensor(room))

        if room.state.value.temperature is not None:
            _LOGGER.info(f"Adding temperature sensor for room {room.name}")
            sensors.append(XComfortEnergySensor(room))

    for device in devices:
        if isinstance(device, RcTouch):
            _LOGGER.info(f"Adding humidity sensor for device {device}")
            sensors.append(XComfortHumiditySensor(device))
            sensors.append(XComfortTemperatureSensor(device))

    _LOGGER.info(f"Added {len(sensors)} rc touch units")
    async_add_entities(sensors)
    return

class XComfortPowerSensor(SensorEntity):
    def __init__(self, room:Room):
        self._attr_device_class = SensorEntityDescription(
            key="current_consumption",
            device_class=SensorDeviceClass.ENERGY,
            native_unit_of_measurement=POWER_WATT,
            state_class=SensorStateClass.MEASUREMENT,
            name="Current consumption",)
        self._room = room
        self._attr_name = self._room.name
        self._attr_unique_id = f"energy_{self._room.room_id}"
        self._state = None
        #self._room.state.subscribe(lambda state: self._state_change(state))

    async def async_added_to_hass(self):
        _LOGGER.warning(f"Added to hass {self._attr_name} ")
        if self._device.state is None:
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

class XComfortEnergySensor(SensorEntity):

    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, room:Room):
        self._attr_device_class = SensorEntityDescription(
            key="energy_used",
            device_class=SensorDeviceClass.ENERGY,
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            state_class=SensorStateClass.TOTAL_INCREASING,
            name="Energy consumption",)
        self._room = room
        self._attr_name = self._room.name
        self._attr_unique_id = f"energy_kwh_{self._room.room_id}"
        self._state = None
        #self._room.state.subscribe(lambda state: self._state_change(state))
        self._updateTime = time.time()
        self._consumption = 0

    async def async_added_to_hass(self):
        _LOGGER.warning(f"Added to hass {self._attr_name} ")
        if self._device.state is None:
            _LOGGER.warning(f"State is null for {self._attr_name}")
        else:
            self._room.state.subscribe(lambda state: self._state_change(state))

    def _state_change(self, state):
        self._state = state
        should_update = self._state is not None
        if should_update:
            self.async_write_ha_state()

    def calculate(self):
        timediff = math.floor(time.time() - self._updateTime)         # number of seconds since last update
        self._consumption += self._state.power / 3600 / 1000 * timediff  # Calculate, in kWh, energy consumption since last update.
        self._updateTime = time.time()

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

    @property
    def native_unit_of_measurement(self):
        return ENERGY_KILO_WATT_HOUR

    @property
    def native_value(self):
        self.calculate()
        return self._consumption


class XComfortHumiditySensor(SensorEntity):
    def __init__(self, room:Room):
        self._attr_device_class = SensorEntityDescription(
            key="humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            name="Humidity",)
        self._room = room
        self._attr_name = self._room.name
        self._attr_unique_id = f"humidity_{self._room.room_id}"
        self._state = None
        #self._room.state.subscribe(lambda state: self._state_change(state))

    async def async_added_to_hass(self):
        _LOGGER.warning(f"Added to hass {self._attr_name} ")
        if self._device.state is None:
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
        self._attr_name = self._room.name
        self._attr_unique_id = f"temperature_{self._room.room_id}"
        self._state = None

    async def async_added_to_hass(self):
        _LOGGER.warning(f"Added to hass {self._attr_name} ")
        if self._device.state is None:
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
