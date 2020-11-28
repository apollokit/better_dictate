import logging
import threading
from typing import Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# dictionary of events for coordination between threads
events: Dict[str, threading.Event] = {
    # event used to signal shutdown across threads
    # once set, this should NEVER BE CLEARED!
    'shutdown': threading.Event(),
    # mouse moved, for signaling parser thread 
    'mouse_moved_parser': threading.Event(),
    # mouse clicked, for signaling parser thread 
    'mouse_clicked_parser': threading.Event(),
    # key pressed, for signaling parser thread 
    'key_pressed_parser': threading.Event()
}

# sleep_event: threading.Event(),

class AppManager:
    """Manages application overall state in a thread safe manner

    All interactions with this class are assumed to be done from threads, so
    the class must internally ensure that all interactions are thread safe
    """

    def __init__(self):
        # indicates sleep mode - when asleep, no speech should be acted on
        self._sleeping = False
        self._sleep_lock = threading.Lock()

    def toggle_sleep(self):
        """Toggle sleep state
        """
        self._sleep_lock.acquire()
        if self._sleeping:
            logger.debug('waking up...')
            self._sleeping = False
        else:
            self._sleeping = True
            logger.debug('going to sleep...')
        self._sleep_lock.release()

    @property
    def sleeping(self) -> bool:
        """Get sleep state
        
        Returns:
            sleep state, True if asleep
        """
        self._sleep_lock.acquire()
        asleep = self._sleeping
        self._sleep_lock.release()
        return asleep


# the global app manager instance
app_mngr = AppManager()

