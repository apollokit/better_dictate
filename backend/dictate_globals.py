from typing import Dict
import threading

# dictionary of events for coordination between threads
events: Dict[str, threading.Event] = {
    # event used to signal shutdown across threads
    # once set, this should NEVER BE CLEARED!
    'shutdown': threading.Event(),
    # indicates sleep mode - when asleep, no speech should be acted on
    'sleep': threading.Event()
}