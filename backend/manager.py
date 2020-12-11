from datetime import datetime, timedelta
import logging
import threading
import time
from typing import Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# sleep_event: threading.Event(),

# After this amount of time, the app manager will automatically put itself to sleep
USER_INTERACTION_TIMEOUT = timedelta(minutes=10)

class AppManager:
    """Manages application overall state in a thread safe manner

    All interactions with this class are assumed to be done from threads, so
    the class must internally ensure that all interactions are thread safe
    """

    def __init__(self):
        # indicates sleep mode - when asleep, no speech should be acted on
        # start asleep at the beginning
        self._sleeping = True
        # the last time the user interacted with the app
        self._last_interaction_timestamp = datetime.utcnow()
        self._interaction_timestamp_lock = threading.Lock()
        self._sleep_lock = threading.Lock()
        # indicates that the app is quitting
        self._quit = False
        self._quit_lock = threading.Lock()

    def user_interacted(self):
        """Signals the app manager that the user interacted with the app
        """
        # maybe this is overly zealous to use a lock here, but just in case
        self._interaction_timestamp_lock.acquire()
        self._last_interaction_timestamp = datetime.utcnow()
        self._interaction_timestamp_lock.release()
    
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

        self.user_interacted()

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

    def signal_quit(self):
        """Signal app to quit
        """
        self._quit_lock.acquire()
        self._quit = True
        logger.debug('quitting...')
        self._quit_lock.release()

    @property
    def quitting(self) -> bool:
        """Get quit state
        
        Returns:
            quit state, True if quitting
        """
        self._quit_lock.acquire()
        quit = self._quit
        self._quit_lock.release()
        return quit

    def manager_thread(self):
        """ Execution read for housekeeping stuff in the manager        
        """

        logger.info("Manager thread ready")
        # the main thread loop. Go forever.
        while True:
            current_time = datetime.utcnow()
            if not self.sleeping and (
                    current_time - self._last_interaction_timestamp 
                        > USER_INTERACTION_TIMEOUT):
                logger.info("Been awhile since interaction, going to sleep...")
                self.toggle_sleep()

            # make sure to sleep so we don't hog things
            time.sleep(1.0)                

class EventManager:
    """A clearinghouse for coordinating events between threads"""
    
    def __init__(self):
        # indicates if we detected a manual end of sentence condition
        self.saw_manual_sentence_end = threading.Event()
        # indicates if a key has been pressed
        self.key_pressed = threading.Event()
        # indicates if the mouse has been clicked
        self.mouse_clicked = threading.Event()

# the global app manager instance
app_mngr = AppManager()
# the global event manager instance
event_mngr = EventManager()

