""" Thread and utilities for audio input.
"""

import logging
import threading
from queue import Queue, Empty

from pynput.keyboard import Controller

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def parser_thread(
        inference_output_q: Queue,
        shutdown_event: threading.Event):
    """ Execution thread for parsing and acting output from inference
    
    Args:
        inference_output_q: contains output string text from the text to speech
            engine.
        shutdown_event: event used to signal shutdown across threads
    """

    # the main thread loop. Go forever.
    keyboard_ctlr = Controller()
    logger.info(f"Parser ready")
    while True:
        try:
            the_text: str = inference_output_q.get(
                block=True, timeout=0.1)
            
            logger.debug(f"Got text from queue: {the_text}")
            
            # the_text = the_text.lower()
            # the_text = the_text.replace(' coma',',')
            # the_text = the_text.replace('coma',',')
            # the_text = the_text.replace(' comma',',')
            # the_text = the_text.replace('comma',',')
            # the_text = the_text.replace(' period','.')
            # the_text = the_text.replace('period','.')
            # the_text = the_text.capitalize()

            keyboard_ctlr.type(the_text)
            
        # queue was empty up to timeout
        except Empty:
            # check if it's time to close shop
            if shutdown_event.is_set(): 
                break
        

