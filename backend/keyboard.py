""" Thread and utilities for audio input.
"""

import logging
import threading

from pynput import keyboard
from pynput.keyboard import Key, Controller

from backend.dictate_globals import shutdown_event

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# event that signals start/stop from the keyboard
keyboard_audio_event = threading.Event()

HOTKEY_MOD = 'alt'
HOTKEY_LET = 'z'

keyboard_ctrlr = Controller()

# counts up till quit/shutdown condition is met
quit_counter = 0
QUIT_COUNT = 3 

# true once the modifier gets pressed
hotkey_primed = False

def on_press(key: keyboard.KeyCode):
    # print('Key {} pressed.'.format(key))
    pass

def on_release(
    key: keyboard.KeyCode):
    """ Takes action upon key release.
    
    Args:
        key: the key that was released
    
    Returns:
        Usually nothing, but False when the thread should be shut down
    """
    global quit_counter
    global hotkey_primed

    # note the escaped quotes. We're checking if the string 
    # is "'<letter>'"
    if hotkey_primed and str(key) == f"\'{HOTKEY_LET}\'":
        hotkey_primed = False
        logger.debug(f'Saw hotkey')
        if not keyboard_audio_event.is_set():
            logger.debug('setting keyboard_audio_event')
            keyboard_audio_event.set()
        else:
            logger.debug('releasing keyboard_audio_event')
            keyboard_audio_event.clear()
    # when pressing modifier + HOTKEY_LET, for some reason there's an on_release
    # for the modifier before the HOTKEY_LET. So just prime it here
    elif HOTKEY_MOD == 'alt' and str(key) == 'Key.alt_r':
        hotkey_primed = True
    elif str(key) == 'Key.esc':
        quit_counter += 1
        if quit_counter >= QUIT_COUNT:
            logger.debug('Exiting keyboard thread...')
            keyboard_audio_event.clear()
            shutdown_event.set()
            return False
    else:
        hotkey_primed = False

keyb_listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)

