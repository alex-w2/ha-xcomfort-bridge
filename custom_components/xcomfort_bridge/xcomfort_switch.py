import logging

from xcomfort.devices import BridgeDevice, DeviceState
from xcomfort.messages import Messages

from .const import VERBOSE

_LOGGER = logging.getLogger(__name__)

def log(msg: str):
    if VERBOSE:
        _LOGGER.info(msg)

class SwitchState(DeviceState):
    def __init__(self, on, payload):
        DeviceState.__init__(self, payload)
        self.on = on

    def __str__(self):
        return f"SwitchState({self.on})"

    __repr__ = __str__

class Switch(BridgeDevice):
    def __init__(self, bridge, device_id, name, comp_id):
        BridgeDevice.__init__(self, bridge, device_id, name)

        self.comp_id = comp_id

    def handle_state(self, payload):
        on = bool(payload['curstate'])
        self.state.on_next(SwitchState(on, payload))

    async def turn_on(self):
        pass # Not implemented

    async def turn_off(self):
        pass # Not implemented

    def __str__(self):
        return f"Switch({self.device_id}, \"{self.name}\", on: {self.state.value.on})"

    __repr__ = __str__