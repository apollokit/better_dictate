""" Functionality for dealing with keyboard interactions
"""

import logging
import threading

from pynput import keyboard
from pynput.keyboard import Key, Controller

from backend.manager import app_mngr, event_mngr

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HOTKEY_MOD = 'ctrl'
HOTKEY_LETTER = 'Key.esc'

SLEEP_COUNT = 2
SLEEP_KEY = 'Key.f2'

# These are all the keys that should *NOT* signal key_pressed_parser_event
# keys_for_parser_disclude = ['Key.right', 'Key.esc']
keys_for_parser = ['Key.enter', 'Key.esc', 'Key.up', 'Key.down', 'Key.tab']

class KeyboardManager():
    # counts up till sleep condition is met
    sleep_counter = 0
    # true once the modifier gets pressed
    hotkey_primed = False
    # we look for the user to type '.' and then ' ' to manually trigger an end
    # of sentence condition
    manual_sentence_end_primed = False


    def on_press(self, key: keyboard.KeyCode):
        # if str(key) in keys_for_parser:
        #     # print("setting key_pressed_parser_event")
        #     key_pressed_parser_event.set()

        event_mngr.key_pressed.set()

    def on_release(self,
        key: keyboard.KeyCode):
        """ Takes action upon key release.

        Args:
            key: the key that was released

        Returns:
            Usually nothing, but False when the thread should be shut down
        """
        keystring = str(key)
        # print(keystring)

        # get rid of single 's when it's a letter keystroke
        if 'Key' not in keystring:
            keystring = keystring[1]

        def clear_state():
            self.sleep_counter = 0
            self.manual_sentence_end_primed = False

        if keystring == SLEEP_KEY:
            self.sleep_counter += 1
            if self.sleep_counter >= SLEEP_COUNT:
                logger.debug('Saw sleep/wake hotkey')
                app_mngr.toggle_sleep()
                clear_state()
        elif keystring == '.':
            self.manual_sentence_end_primed = True
        elif keystring == 'Key.space':
            if self.manual_sentence_end_primed:
                event_mngr.saw_manual_sentence_end.set()
                clear_state()
        else:
            clear_state()
            event_mngr.saw_manual_sentence_end.clear()

kb_mngr = KeyboardManager()

keyb_listener = keyboard.Listener(
    on_press=kb_mngr.on_press,
    on_release=kb_mngr.on_release)

