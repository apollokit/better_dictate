import logging

from pynput.keyboard import Controller

from backend.manager import event_mngr
from backend.text_formatter import PlainTextFormatter, CodeTextFormatter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# formatters four different modes of the text writer
formatters = {
    'plaintext': PlainTextFormatter(),
    'code': CodeTextFormatter()
}

class TextWriter:
    """Handles riding out raw text in long-form dictation"""
    
    # the different text formatting modes
    MODES = ['code', 'plaintext']

    def __init__(self):
        self._keyboard_ctlr = Controller()
        # start in plain text mode
        self.mode = 'plaintext'

    def dispatch(self, raw: str):
        """write some text out
        
        Args:
            raw: the raw text output from the speech-to-text engine, before 
                formatting
        """
        logger.debug("Raw text: '%s'", raw)
       
        curr_formatter = formatters[self.mode]
        formatted = curr_formatter.format(raw)
        
        logger.debug("Typing: '%s'", formatted)
        self._keyboard_ctlr.type(formatted)

        ## clear user action state
        # note we need to do this after typing out anything with the 
        # keyboard controller!
        event_mngr.mouse_clicked.clear()
        event_mngr.key_pressed.clear()
        event_mngr.saw_manual_sentence_end.clear()