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
from .rctouch import RcTouch
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ENERGY_KILO_WATT_HOUR,
    PERCENTAGE,
    POWER_WATT,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    hub = XComfortHub.get_hub(hass, entry)

    devices = hub.devices

    _LOGGER.info(f"Found {len(devices)} xcomfort devices")

    sensors= list()
    for device in devices:
        if isinstance(device,RcTouch):
            _LOGGER.info(f"Adding {device}")
            sensors.append(XComfortPowerSensor(device))
            sensors.append(XComfortEnergySensor(device))
            sensors.append(XComfortHumiditySensor(device))

    _LOGGER.info(f"Added {len(sensors)} rc touch units")
    async_add_entities(sensors)
    return

class XComfortPowerSensor(SensorEntity):
    def __init__(self, device:RcTouch):
        self._attr_device_class = SensorEntityDescription(
            key="current_consumption",
            device_class=SensorDeviceClass.ENERGY,
            native_unit_of_measurement=POWER_WATT,
            state_class=SensorStateClass.MEASUREMENT,
            name="Current consumption",)
        self._device = device
        self._attr_name = self._device.name
        self._attr_unique_id = f"energy_{self._device.name}_{self._device.device_id}"
        self._state = None
        self._device.state.subscribe(lambda state: self._state_change(state))

    def _state_change(self, state):

        should_update = self._state is not None

        self._state = state
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

    def __init__(self, device:RcTouch):
        self._attr_device_class = SensorEntityDescription(
            key="energy_used",
            device_class=SensorDeviceClass.ENERGY,
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            state_class=SensorStateClass.TOTAL_INCREASING,
            name="Energy consumption",)
        self._device = device
        self._attr_name = self._device.name
        self._attr_unique_id = f"energy_kwh_{self._device.name}_{self._device.device_id}"
        self._state = None
        self._device.state.subscribe(lambda state: self._state_change(state))
        self._updateTime = time.time()
        self._consumption = 0

    def _state_change(self, state):

        should_update = self._state is not None
        self._state = state
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
    def __init__(self, device:RcTouch):
        self._attr_device_class = SensorEntityDescription(
            key="humidity",
            device_class=SensorDeviceClass.ENERGY,
            native_unit_of_measurement=POWER_WATT,
            state_class=SensorStateClass.MEASUREMENT,
            name="Humidity",)
        self._device = device
        self._attr_name = self._device.name
        self._attr_unique_id = f"humidity_{self._device.name}_{self._device.device_id}"
        self._state = None
        self._device.state.subscribe(lambda state: self._state_change(state))

    def _state_change(self, state):

        should_update = self._state is not None

        self._state = state
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
        return self._state.current_humidity