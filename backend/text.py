import logging

from pynput.keyboard import Controller

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

    def dispatch(self, raw: str, saw_user_action: bool):
        """write some text out
        
        Args:
            raw: the raw text output from the speech-to-text engine, before 
                formatting
            saw_user_action: flag to indicate that the user took some action 
                before this utterance.
        """
        logger.debug("Raw text: '%s'", raw)
       
        curr_formatter = formatters[self.mode]
        curr_formatter.saw_user_action = saw_user_action
        formatted = curr_formatter.format(raw)
        
        logger.debug("Typing: '%s'", formatted)
        self._keyboard_ctlr.type(formatted)