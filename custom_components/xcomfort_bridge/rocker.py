import logging

from .const import VERBOSE

_LOGGER = logging.getLogger(__name__)

def log(msg: str):
    if VERBOSE:
        _LOGGER.warning(msg)

class Rocker:
    def __init__(self, bridge, device_id, name, device):
        self.bridge = bridge
        self.device_id = device_id
        self._device = device
        self.name = name
