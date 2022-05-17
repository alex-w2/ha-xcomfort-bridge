import logging
from aiohttp import Payload
import rx

from .const import VERBOSE

_LOGGER = logging.getLogger(__name__)

def log(msg: str):
    if VERBOSE:
        _LOGGER.warning(msg)

class WindowShade:
    def __init__(self, bridge, device_id, name, device, state):
        self.bridge = bridge
        self.device_id = device_id
        self._device = device
        self.name = name
        self.state = rx.subject.BehaviorSubject(state)

class WindowShadeState:
    def __init__(self, shPos, shSlatPos):
        self.current_cover_position = 100 - shPos
        self.current_cover_tilt_position = 255 - shSlatPos

    def __str__(self):
        return f"WindowShadeState({self.current_cover_position}, {self.current_cover_tilt_position})"

    __repr__ = __str__
