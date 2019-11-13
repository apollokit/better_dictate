""" Thread and utilities for audio input.
"""

import logging
import threading

from pynput import keyboard
from pynput.keyboard import Key, Controller

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HOTKEY_MOD = 'alt'
HOTKEY_LET = 'z'

keyboard_ctrlr = Controller()

quit_counter = 0
QUIT_COUNT = 3

def keyboard_on_press(key: keyboard.KeyCode):
    pass
    # print('Key {} pressed.'.format(key))

def keyboard_on_release(
    key: keyboard.KeyCode, 
    audio_ctrl: threading.Event):
    """ Takes action upon key release.
    
    Args:
        key: the key that was released
        audio_ctrl:  Control for the audio thread. Should be set here so
            the audio thread can go do work
    
    Returns:
        Usually nothing, but False when the thread should be shut down
    """
    # logging.debug('Key {} released.'.format(key))
    if HOTKEY_MOD == 'alt' and keyboard_ctrlr.alt_pressed:
        # note the escaped quotes. We're checking if the string 
        # is "'<letter>'"
        if str(key) == f"\'{HOTKEY_LET}\'":
            logging.debug('Saw hotkey')
            if not audio_ctrl.is_set():
                print('setting audio_ctrl')
                audio_ctrl.set()
            else:
                print('releasing audio_ctrl')
                audio_ctrl.clear()
    if str(key) == 'Key.esc':
        quit_counter += 1
        if quit_counter >= QUIT_COUNT:
            print('Exiting keyboard thread...')
            return False
