from typing import Dict
import threading

# dictionary of events for coordination between threads
events: Dict[str, threading.Event] = {
    # event used to signal shutdown across threads
    # once set, this should NEVER BE CLEARED!
    'shutdown': threading.Event(),
    # indicates sleep mode - when asleep, no speech should be acted on
    'sleep': threading.Event(),
    # mouse moved, for signaling parser thread 
    'mouse_moved_parser': threading.Event(),
    # mouse clicked, for signaling parser thread 
    'mouse_clicked_parser': threading.Event(),
    # key pressed, for signaling parser thread 
    'key_pressed_parser': threading.Event()
}