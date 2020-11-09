""" Thread and utilities for audio input.
"""

import logging
import threading

from pynput import keyboard
from pynput.keyboard import Key, Controller

from backend.dictate_globals import events

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HOTKEY_MOD = 'ctrl'
HOTKEY_LETTER = 'Key.esc'

keyboard_ctrlr = Controller()

QUIT_COUNT = 3 


sleep_event = events['sleep']

class KeyboardManager():
    # counts up till quit/shutdown condition is met
    quit_counter = 0
    # true once the modifier gets pressed
    hotkey_primed = False


    def on_press(self, key: keyboard.KeyCode):
        # print('Key {} pressed.'.format(key))
        pass

    def on_release(self,
        key: keyboard.KeyCode):
        """ Takes action upon key release.
        
        Args:
            key: the key that was released
        
        Returns:
            Usually nothing, but False when the thread should be shut down
        """

        def clear_state():
            self.hotkey_primed = False
            self.quit_counter = 0

        # print(str(key))
        # print(f"\'{HOTKEY_LETTER}\'")
        # print(str(key) == f"\'{HOTKEY_LETTER}\'")

        ## sleep/wake (right Control then Escape)
        if self.hotkey_primed and str(key) == f"{HOTKEY_LETTER}":
            logger.debug('Saw sleep/wake hotkey')
            if not sleep_event.is_set():
                logger.debug('going to sleep...')
                sleep_event.set()
            else:
                logger.debug('waking up...')
                sleep_event.clear()
            clear_state()
        ## Look for right alt key to be pressed
        # when pressing modifier + HOTKEY_LETTER, for some reason there's an on_release
        # for the modifier before the HOTKEY_LETTER. So just prime it here
        elif HOTKEY_MOD == 'ctrl' and str(key) == 'Key.ctrl_r':
            self.hotkey_primed = True
        ## shut down - Escape three times in a row
        elif str(key) == 'Key.esc':
            self.quit_counter += 1
            if self.quit_counter >= QUIT_COUNT:
                logger.debug('Exiting keyboard thread...')
                events['shutdown'].set()
                return False
        else:
            clear_state()

kb_mngr = KeyboardManager()

keyb_listener = keyboard.Listener(
    on_press=kb_mngr.on_press,
    on_release=kb_mngr.on_release)

