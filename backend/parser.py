""" Thread and utilities for audio input.
"""

import logging
import threading
from queue import Queue, Empty
from typing import Dict

from pynput.keyboard import Controller

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
        shutdown_event = events['shutdown']
        logger.info("Parser ready")
        while True:
            try:
                the_text: str = raw_stt_output_q.get(
                    block=True, timeout=0.1)
                
                logger.debug(f"Got text from queue: '{the_text}'")
                
                the_text = the_text.lower()
                the_text = the_text.strip()
                print(the_text)
                last_char = the_text[-1:]
                #  if was end of sentence last time, format it
                if self.saw_end_of_sentence:
                    the_text = the_text.capitalize()
                    the_text = " " + the_text
                # check if currently the end of sentence
                if last_char in ['?','.','!']:
                    self.saw_end_of_sentence = True
                else:
                    self.saw_end_of_sentence = False
                    # add a space to continue the sentence
                    the_text += " "

                logger.debug(f"Typing: '{the_text}'")
                keyboard_ctlr.type(the_text)
                
            # queue was empty up to timeout
            except Empty:
                # check if it's time to close shop
                if shutdown_event.is_set(): 
                    break
            

