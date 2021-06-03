import logging
import time

from pynput.keyboard import Controller, Key

from backend.manager import event_mngr
from backend.text_formatter import PlainTextFormatter, CodeTextFormatter
from backend.actions import Action
from ui.kb_controller import KBCntrlrWrapper

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# formatters four different modes of the text writer
formatters = {
    'plaintext': PlainTextFormatter(),
    'code': CodeTextFormatter()
}

class TextWriteAction(Action):
    """Action for writing text
    """

    def __init__(self, text: str, kb_controller: KBCntrlrWrapper):
        """Init

        Args:
            text: the text written by this action
        """
        self.text = text
        self._kb_controller = kb_controller

    def undo(self) -> bool:
        """Undo the text writing action

        Deletes all the characters written

        Returns:
            True, because this action is "substantial". See
                documentation for Action() for more information
        """
        logger.debug('TextWriteAction: undo, deleting text {}'.format(self.text))
        for char in self.text: #pylint: disable=unused-variable
            self._kb_controller.tap(Key.backspace)
        return True

class TextWriter:
    """Handles riding out raw text in long-form dictation"""

    # the different text formatting modes
    MODES = ['code', 'plaintext']

    def __init__(self, kb_controller: KBCntrlrWrapper):
        self._kb_controller = kb_controller
        # start in plain text mode
        self.mode = 'plaintext'

    def dispatch(self, raw: str) -> Action:
        """write some text out

        Args:
            raw: the raw text output from the speech-to-text engine, before
                formatting

        Returns:
            an action
        """
        logger.debug("Raw text: '%s'", raw)

        curr_formatter = formatters[self.mode]
        formatted = curr_formatter.format(raw)

        # special format characters that need some sleep time added in
        special_format_chars = ['`', '}']

        logger.debug("Typing: '%s'", formatted)
        next_iter_do_sleep = False
        for char in formatted:
            # insert some sleep so we can trigger the application in which the typing is being done to format correctly
            # for example, if we just spit out all the text at once, in slack
            # we could end up with the literal "`blah`" instead of "<blah
            # formatted as code>"
            if next_iter_do_sleep:
                # time.sleep(0.1) # this is sufficient for slack
                time.sleep(0.2) # but need this for atlassian confluence
                next_iter_do_sleep = False
            if char in special_format_chars:
                next_iter_do_sleep = True
            self._kb_controller.tap(char)

        ## clear user action state
        # note we need to do this after typing out anything with the
        # keyboard controller!
        event_mngr.mouse_clicked.clear()
        event_mngr.mouse_doubleclicked.clear()
        event_mngr.key_pressed.clear()
        event_mngr.saw_manual_sentence_end.clear()

        return TextWriteAction(formatted, self._kb_controller)
