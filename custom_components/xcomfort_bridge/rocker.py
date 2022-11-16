import logging, traceback

from xcomfort.bridge import BridgeDevice

from .const import VERBOSE

_LOGGER = logging.getLogger(__name__)

def log(msg: str):
    if VERBOSE:
        _LOGGER.warning(msg)

class Rocker(BridgeDevice):
    def __init__(self, bridge, device_id, name, comp_id):
        BridgeDevice.__init__(self, bridge, device_id, name)

        self.bridge = bridge
        self.device_id = device_id
        self.comp_id = comp_id
        self.name = name

    def handle_state(self, payload):
        try:
            if 'curstate' in payload:
                if self.comp_id in self.bridge._comps:
                    comp = self.bridge._comps[self.comp_id]
                    curstate = payload['curstate']
                    log(f"Rocker {comp.name} {self.name} toggled: {curstate}")
                    self.bridge.bus.fire(f"xcomfort_rocker_{comp.name} {self.name}", {"state": int(curstate) })
                else:
                    log(f"Comp {self.compId} not found in {repr(self.bridge._comps)}")
        except:
            log(f"Failed to update device '{self.device_id}'. Error: {traceback.format_exc()} Payload: {repr(payload)}")

    def __str__(self):
        return f"Rocker({self.device_id}, \"{self.name}\")"