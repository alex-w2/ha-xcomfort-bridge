"""Support for Xcomfort sensors."""

from __future__ import annotations

import time
import math
import logging
from typing import cast

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from xcomfort.bridge import Room
from xcomfort.devices import RcTouch

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ENERGY_KILO_WATT_HOUR,
    ENERGY_WATT_HOUR,
    PERCENTAGE,
    TEMP_CELSIUS,
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import XComfortHub

_LOGGER = logging.getLogger(__name__)


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

            if room.state.value.temperature is not None:
                _LOGGER.info(f"Adding temperature sensor for room {room.name}")
                sensors.append(XComfortEnergySensor(room))

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
            native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
            state_class=SensorStateClass.MEASUREMENT,
            name="Current consumption",
        )
        self._room = room
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
        return UnitOfEnergy.WATT_HOUR

    @property
    def native_value(self):
        return self._state and self._state.power


class XComfortEnergySensor(RestoreSensor):
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(self, room: Room):
        self._attr_device_class = SensorEntityDescription(
            key="energy_used",
            device_class=SensorDeviceClass.ENERGY,
            native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            state_class=SensorStateClass.TOTAL_INCREASING,
            name="Energy consumption",
        )
        self._room = room
        self._attr_name = self._room.name
        self._attr_unique_id = f"energy_kwh_{self._room.room_id}"
        self._state = None
        self._room.state.subscribe(lambda state: self._state_change(state))
        self._updateTime = time.time()
        self._consumption = 0

    async def async_added_to_hass(self) -> None:
        """Call when entity about to be added to hass."""
        await super().async_added_to_hass()
        savedstate = await self.async_get_last_sensor_data()
        if savedstate:
            self._consumption = cast(float, savedstate.native_value)

    def _state_change(self, state):
        should_update = self._state is not None
        self._state = state
        if should_update:
            self.async_write_ha_state()

    def calculate(self):
        timediff = math.floor(
            time.time() - self._updateTime
        )  # number of seconds since last update
        self._consumption += (
            self._state.power / 3600 / 1000 * timediff
        )  # Calculate, in kWh, energy consumption since last update.
        self._updateTime = time.time()

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

    @property
    def native_unit_of_measurement(self):
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def native_value(self):
        self.calculate()
        return self._consumption


class XComfortHumiditySensor(SensorEntity):
    def __init__(self, room: Room):
        self._attr_device_class = SensorEntityDescription(
            key="humidity",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            name="Humidity",
        )
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
        return self._state and self._state.humidity


class XComfortTemperatureSensor(SensorEntity):
    def __init__(self, room: Room):
        self._attr_device_class = SensorEntityDescription(
            key="temperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=TEMP_CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            name="Temperature",
        )
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
