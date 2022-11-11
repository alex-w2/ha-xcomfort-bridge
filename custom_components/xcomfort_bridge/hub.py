"""Class used to communicate with xComfort bridge."""

from __future__ import annotations

import asyncio
import logging
import traceback

from xcomfort.bridge import Bridge, State
from xcomfort.devices import Light, LightState
from .rocker import Rocker

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, EventBus

from .const import DOMAIN, VERBOSE

_LOGGER = logging.getLogger(__name__)

"""Logging function."""
def log(msg: str):
    if VERBOSE:
        _LOGGER.warning(msg)


"""Wrapper class over bridge library to emulate hub."""
class XComfortHub:
    def __init__(self, hass: HomeAssistant, identifier: str, ip: str, auth_key: str):
        """Initialize underlying bridge"""
        bridge = Bridge(ip, auth_key)
        self.bridge = bridge
        self.identifier = identifier
        if self.identifier is None:
            self.identifier = ip
        self._id = ip
        self.devices = list()
        log("getting event loop")
        self._loop = asyncio.get_event_loop()

    def start(self):
        """Starts the event loop running the bridge."""
        asyncio.create_task(self.bridge.run())

    async def stop(self):
        """Stops the bridge event loop.
        Will also shut down websocket, if open."""
        await self.bridge.close()

    async def load_devices(self):
        """Loads devices from bridge."""
        log("loading devices")
        devs = await self.bridge.get_devices()
        self.devices = devs.values()

        log(f"loaded {len(self.devices)} devices")

        log("loading rooms")

        rooms = await self.bridge.get_rooms()
        self.rooms = rooms.values()

        log(f"loaded {len(self.rooms)} rooms")

    @property
    def hub_id(self) -> str:
        return self._id

    async def test_connection(self) -> bool:
        await asyncio.sleep(1)
        return True

    @staticmethod
    def get_hub(hass: HomeAssistant, entry: ConfigEntry) -> XComfortHub:
        return hass.data[DOMAIN][entry.entry_id]

# Not currently used, but needs some manual merging after
#"""Low-level library that handles incoming data from websocket."""
"""
class XComfortBridge(Bridge):
    def __init__(self, bus: EventBus, ip_address: str, authkey: str, session=None):
        super().__init__(ip_address, authkey, session)
        self._devicelist = {}
        self._roomHeatinglist = {}
        self._comps = {}
        self.logger = lambda x: log(x)
        self.bus = bus

    def _add_device(self, device):
        self._devices[device.device_id] = device

    def _handle_SET_STATE_INFO(self, payload):
        for item in payload['item']:
            if 'deviceId' in item:
                deviceId = item['deviceId']
                if deviceId in self._devices:
                    device = self._devices[deviceId]
                    try:
                        # Sample light switch JSON payload
                        # {'item': [{'deviceId': 142, 'dimmvalue': 0, 'switch': False}, {'deviceId': 142, 'info': [{'text': '1109', 'type': 2, 'icon': 1, 'value': '39'}]}]}
                        if isinstance(device, Light) and 'switch' in item and 'dimmvalue' in item:
                            device.state.on_next(LightState(item['switch'], item['dimmvalue']))
                        if isinstance(device, RcTouch):
                            device.state.on_next(RcTouchState(payload))
                        # Sample window shade JSON payload
                        #  {'item': [{'deviceId': 10116, 'curstate': 1, 'shPos': 16, 'shSlatPos': 255, 'shCalInfo': 1}, {'deviceId': 10116, 'info': [{'text': '1109', 'type': 2, 'icon': 1, 'value': '17'}, {'text': '1132', 'type': 1, 'value': '16%'}]}]}
                        if isinstance(device, WindowShade) and 'shPos' in item and 'shSlatPos' in item:
                            device.state.on_next(WindowShadeState(item['shPos'], item['shSlatPos']))
                        if isinstance(device, Rocker) and 'curstate' in item:
                            curstate = item['curstate']
                            log(f"Rocker {device.name} toggled: {curstate}")
                            self.bus.fire(f"xcomfort_rocker_{device.name}", {"state": int(curstate) })
                    except:
                        log(f"Failed to update device '{deviceId}'. Error: {traceback.format_exc()} Payload: {repr(payload)}")

    def _handle_SET_ALL_DATA(self, payload):
        if "devices" in payload:
            for device in payload["devices"]:
                self._devicelist[device['deviceId']] = device
        if "roomHeating" in payload:
            for rh in payload["roomHeating"]:
                if 'roomId' in rh:
                    roomId = rh['roomId']
                    log(f"Updating room heating for room '{roomId}'")
                    self._roomHeatinglist[roomId] = rh
                    if 'power' in rh and 'setpoint' in rh and 'currentMode' in rh:
                        state = RcTouchState(rh, float(rh['power']), float(rh['setpoint']), rh['currentMode'])
                        device_id = rh['roomSensorId']
                        thing = self._devices.get(device_id)
                        if thing is not None:
                            log(f"updating rc touch {device_id},{thing.name} {state}")
                            thing.state.on_next(state)
        if "comps" in payload:
            for comp in payload["comps"]:
                self._comps[comp['compId']] = comp

    def _handle_SET_HOME_DATA(self, payload):
        for device in self._devicelist.values():
            try:
                device_id = device["deviceId"]
                name = device["name"]
                dev_type = device["devType"]
                # Add new devices with initial state only,
                # don't update existing devices with stale data
                if dev_type == 100 or dev_type == 101:
                    thing = self._devices.get(device_id)
                    if thing is None:
                        state = LightState(device["switch"], device["dimmvalue"])
                        log(f"adding light {device_id}, {name} {state}")
                        light = Light(self, device_id, name, device["dimmable"], state)
                        self._add_device(light)
                elif dev_type == 102:
                    thing = self._devices.get(device_id)
                    if thing is None:
                        state = WindowShadeState(device['shPos'], device['shSlatPos'])
                        log(f"adding window shade {device_id}, {name} {state}")
                        shade = WindowShade(self, device_id, name, device, state)
                        self._add_device(shade)
                elif dev_type == 220:
                    log(f"Device 220: {device}")
                    thing = self._devices.get(device_id)
                    if thing is None and 'compId' in device:
                        compId = device['compId']
                        if compId in self._comps:
                            comp = self._comps[compId]
                            name = f"{comp['name']} {name}"
                            log(f"adding rocker {device_id}, {name}")
                            rocker = Rocker(self, device_id, name, device)
                            self._add_device(rocker)
                elif dev_type == 450:
                    thing = self._devices.get(device_id)
                    if thing is None:
                        rh = self.getRoomHeating(device_id)
                        state = RcTouchState(device, float(rh['power']), float(rh['setpoint']), rh['currentMode'])
                        log(f"adding rc touch {device_id}, {name} {state}")
                        rctouch = RcTouch(self,device_id ,name, device, state)
                        self._add_device(rctouch)
                else:
                    log(f"Unknown device type {dev_type} named '{name}' - Skipped")
            except:
                log(f"Failed to add device '{device_id}'. Error: {traceback.format_exc()} Payload: {repr(payload)}")

        self.state = State.Ready

    def _handle_SET_BRIDGE_STATE(self, payload):
        pass

    def _handle_SET_ROOM_HEATING_STATE(self, payload):
        pass

    def getComp(self, compId):
        for comp in self._comps.values():
            if comp["compId"] == compId:
                return comp

    def getRoomHeating(self, sensorId):
        for rh in self._roomHeatinglist.values():
            if rh["roomSensorId"] == sensorId:
                return rh
"""