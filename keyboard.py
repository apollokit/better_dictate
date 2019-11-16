""" Thread and utilities for audio input.
"""

import logging
import threading

from pynput import keyboard
from pynput.keyboard import Key, Controller

from dictate_globals import shutdown_event

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# event that signals start/stop from the keyboard
keyboard_audio_event = threading.Event()

HOTKEY_MOD = 'alt'
HOTKEY_LET = 'z'

keyboard_ctrlr = Controller()

quit_counter = 0
QUIT_COUNT = 3

def on_press(key: keyboard.KeyCode):
    pass
    # print('Key {} pressed.'.format(key))

def on_release(
    key: keyboard.KeyCode):
    """ Takes action upon key release.
    
    Args:
        key: the key that was released
    
    Returns:
        Usually nothing, but False when the thread should be shut down
    """
    global quit_counter
    # logging.debug('Key {} released.'.format(key))
    # if HOTKEY_MOD == 'alt' and keyboard_ctrlr.alt_pressed:
        # print('yo')
        # note the escaped quotes. We're checking if the string 
        # is "'<letter>'"
    if str(key) == f"\'{HOTKEY_LET}\'":
        logger.debug(f'Saw hotkey')
        if not keyboard_audio_event.is_set():
            logger.debug('setting keyboard_audio_event')
            keyboard_audio_event.set()
        else:
            logger.debug('releasing keyboard_audio_event')
            keyboard_audio_event.clear()
    if str(key) == 'Key.esc':
        quit_counter += 1
        if quit_counter >= QUIT_COUNT:
            logger.debug('Exiting keyboard thread...')
            keyboard_audio_event.clear()
            shutdown_event.set()
            return False

keyb_listener = keyboard.Listener(
    press=on_press,
    on_release=on_release)

