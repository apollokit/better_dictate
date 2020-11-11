""" Thread and utilities for audio input.
"""

import logging
import threading
from queue import Queue, Empty
from typing import Dict

from pynput.keyboard import Controller

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

END_OF_SENTENCE_CHARS = ['?','.','!']

class DictateParser:
    saw_end_of_sentence = False

    def parser_thread(self,
            raw_stt_output_q: Queue,
            events: Dict[str, threading.Event]):
        """ Execution thread for parsing and acting output from inference
        
        Args:
            raw_stt_output_q: contains output string text from the text to speech
                engine.
            events: dictionary of events for coordination between threads
        """

        # the main thread loop. Go forever.
        keyboard_ctlr = Controller()
        
        # events
        shutdown_event = events['shutdown']
        key_pressed_event = events['key_pressed_parser']
        mouse_clicked_event = events['mouse_clicked_parser']

        logger.info("Parser ready")
        while True:
            try:
                # get raw text from the queue
                the_text: str = raw_stt_output_q.get(
                    block=True, timeout=0.1)
                
                # check if there was a user action since last time 
                saw_user_action = mouse_clicked_event.is_set() or \
                    key_pressed_event.is_set()
                if saw_user_action:
                    self.saw_end_of_sentence = False

                logger.debug(f"Got: '{the_text}'")
                logger.debug(f"Saw mouse_clicked_event: {mouse_clicked_event.is_set()}")
                logger.debug(f"Saw key_pressed_event: {key_pressed_event.is_set()}")
                
                the_text = the_text.lower()
                the_text = the_text.strip()
                last_char = the_text[-1:]
                logger.debug(f"Step 1: '{the_text}'")
                
                ## Handle spaces 1

                # explicitly mark that we need to add a space, if "space bar" 
                # precedes everything else
                explicit_space_add = False
                if the_text[:10] in ['space bar ']:
                    the_text = the_text[10:]
                    explicit_space_add = True
                if the_text[:9] in ['spacebar ']:
                    the_text = the_text[9:]
                    explicit_space_add = True
                logger.debug(f"Step 2: '{the_text}'")

                ## Handle capitalization

                # Capitalize, if it begins with "capital/capitol"
                if the_text[:8] in ['capital ', 'capitol ']:
                    the_text = the_text[8:]
                    the_text = the_text.capitalize()
                logger.debug(f"Step 3: '{the_text}'")

                # Only do this automatic capitalization if we saw the end of a 
                # sentence
                if self.saw_end_of_sentence:
                    the_text = the_text.capitalize()
                logger.debug(f"Step 4: '{the_text}'")

                ## Handle spaces 2

                # There should be a leading space if:
                # - There was no user action such that we're "typing in a new place", 
                # - The text is more than one character long.
                # - There's an explicit space add
                if (not saw_user_action and len(the_text) > 1) or explicit_space_add:
                    the_text = " " + the_text
                logger.debug(f"Step 5: '{the_text}'")
                
                # check if currently the end of sentence
                if last_char in END_OF_SENTENCE_CHARS:
                    self.saw_end_of_sentence = True
                else:
                    self.saw_end_of_sentence = False
                #     # add a space to continue the sentence
                #     the_text += " "
                logger.debug(f"Step 6: '{the_text}'")

                # replace specific patterns
                the_text = the_text.replace(" i ", " I ")
                the_text = the_text.replace("i've", "I've")
                the_text = the_text.replace("quote", '"')
                # for backticks
                the_text = the_text.replace("backslider", '`')
                the_text = the_text.replace("back slider", '`')
                # # replace "space" with " "
                # the_text = the_text.replace(" space ", ' ')
                logger.debug(f"Step 7: '{the_text}'")

                logger.debug(f"Typing: '{the_text}'")
                keyboard_ctlr.type(the_text)

                ## clear user action state
                # note we need to do this after typing out anything with the 
                # keyboard controller!
                mouse_clicked_event.clear()
                key_pressed_event.clear()
                
            # queue was empty up to timeout
            except Empty:
                # check if it's time to close shop
                if shutdown_event.is_set(): 
                    break
            

