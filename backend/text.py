import logging
from typing import Dict

from pynput.keyboard import Controller

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

END_OF_SENTENCE_CHARS = ['?','.','!']

class TextWriter:
    def __init__(self):
        # did we see an end of sentence at the end of the last utterance?
        self.saw_end_of_sentence = False
        # number words that have been written out
        self.count_words_out = 0

        self.keyboard_ctlr = Controller()

    def dispatch(self, raw: str, saw_user_action: bool):
        logger.debug("Raw text: '{}'".format(raw))
        
        if saw_user_action:
            self.saw_end_of_sentence = False

        the_text = raw
        the_text = the_text.lower()
        the_text = the_text.strip()
        last_char = the_text[-1:]
        logger.debug("Step 1: '{}'".format(the_text))
        
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
        logger.debug("Step 2: '{}'".format(the_text))

        ## Handle capitalization

        # Capitalize, if it begins with "capital/capitol"
        if the_text[:8] in ['capital ', 'capitol ']:
            the_text = the_text[8:]
            the_text = the_text.capitalize()
        logger.debug("Step 3: '{}'".format(the_text))

        # Only do this automatic capitalization if we saw the end of a 
        # sentence
        if self.saw_end_of_sentence:
            the_text = the_text.capitalize()
        logger.debug("Step 4: '{}'".format(the_text))

        ## Handle spaces 2

        # There should be a leading space if:
        # - There was no user action such that we're "typing in a new place", 
        # - The text is more than one character long.
        # - There's an explicit space add
        if (not saw_user_action and len(the_text) > 1) or explicit_space_add:
            the_text = " " + the_text
        logger.debug("Step 5: '{}'".format(the_text))
        
        # check if currently the end of sentence
        if last_char in END_OF_SENTENCE_CHARS:
            self.saw_end_of_sentence = True
        else:
            self.saw_end_of_sentence = False
        #     # add a space to continue the sentence
        #     the_text += " "
        logger.debug("Step 6: '{}'".format(the_text))

        # replace specific patterns
        the_text = the_text.replace(" i ", " I ")
        the_text = the_text.replace("i've", "I've")
        the_text = the_text.replace("quote", '"')
        # for backticks
        the_text = the_text.replace("backslider", '`')
        the_text = the_text.replace("back slider", '`')
        # # replace "space" with " "
        # the_text = the_text.replace(" space ", ' ')
        logger.debug("Step 7: '{}'".format(the_text))

        logger.debug("Typing: '{}'".format(the_text))
        self.keyboard_ctlr.type(the_text)