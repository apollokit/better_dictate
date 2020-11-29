""" Functionality for dealing with keyboard interactions 
"""

import logging
import threading

from pynput import keyboard
from pynput.keyboard import Key, Controller

from backend.manager import events, app_mngr

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HOTKEY_MOD = 'ctrl'
HOTKEY_LETTER = 'Key.esc'

keyboard_ctrlr = Controller()

QUIT_COUNT = 5
SLEEP_COUNT = 3

# These are all the keys that should *NOT* signal key_pressed_parser_event
# keys_for_parser_disclude = ['Key.right', 'Key.esc']
keys_for_parser = ['Key.enter', 'Key.esc', 'Key.up', 'Key.down', 'Key.tab']

key_pressed_parser_event = events['key_pressed_parser']

class KeyboardManager():
    # counts up till sleep condition is met
    sleep_counter = 0
    # true once the modifier gets pressed
    hotkey_primed = False


    def on_press(self, key: keyboard.KeyCode):
        # if str(key) in keys_for_parser:
        #     # print("setting key_pressed_parser_event")
        #     key_pressed_parser_event.set()

        key_pressed_parser_event.set()

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
            self.sleep_counter = 0

        # print(str(key))
        # print(f"\'{HOTKEY_LETTER}\'")
        # print(str(key) == f"\'{HOTKEY_LETTER}\'")

        ## sleep/wake (right Control then Escape)
        if self.hotkey_primed and str(key) == f"{HOTKEY_LETTER}":
            pass
        ## Look for right alt key to be pressed
        # when pressing modifier + HOTKEY_LETTER, for some reason there's an on_release
        # for the modifier before the HOTKEY_LETTER. So just prime it here
        elif HOTKEY_MOD == 'ctrl' and str(key) == 'Key.ctrl_r':
            self.hotkey_primed = True
        elif str(key) == 'Key.esc':
            self.sleep_counter += 1
            if self.sleep_counter >= SLEEP_COUNT:
                logger.debug('Saw sleep/wake hotkey')                    
                app_mngr.toggle_sleep()
                clear_state()
        else:
            clear_state()

kb_mngr = KeyboardManager()

keyb_listener = keyboard.Listener(
    on_press=kb_mngr.on_press,
    on_release=kb_mngr.on_release)

