import logging
from typing import Dict

from pynput.keyboard import Controller

from backend.text_formatter import PlainTextFormatter, CodeTextFormatter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


formatters = {
    'plaintext': PlainTextFormatter(),
    'code': CodeTextFormatter()
}

class TextWriter:
    MODES = ['code', 'plaintext']

    def __init__(self):
        
        self._keyboard_ctlr = Controller()

        self.mode = 'plaintext'

    def dispatch(self, raw: str, saw_user_action: bool):
        logger.debug("Raw text: '%s'", raw)
       
        curr_formatter = formatters[self.mode]
        curr_formatter.saw_user_action = saw_user_action
        formatted = curr_formatter.format(raw)
        
        logger.debug("Typing: '%s'", formatted)
        self._keyboard_ctlr.type(formatted)