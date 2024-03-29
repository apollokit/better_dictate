from os import path
import logging

import yaml

from backend.manager import event_mngr

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

END_OF_SENTENCE_CHARS = ['?','.','!']

class TextFormatter:
    """Handles correct formatting of text for output
    """

    # this is the file with hard-coded patterns of text to drop in and replace
    # hard-code the replace patterns file for now
    replace_patterns_file = path.join(path.dirname(__file__),
        'replace_patterns.yml')

    def __init__(self):
        # controls handling of whitespace removal around ()
        self._remove_space_before_open_paren = False
        self._remove_space_after_close_paren = False

        with open(self.replace_patterns_file, 'r') as f:
            self._fixed_replace_patterns = yaml.load(f, Loader=yaml.FullLoader)

    def _log_step(self, step: int, the_text: str):
        """log a step in the formatting process to output
        
        Args:
            step: which step we're at in the formatting process
            the_text: the text to log
        """
        logger.debug("Step %d: '%s'", step, the_text)
        # print("Step %d: '%s'", step, the_text)
    
    def format(self, raw: str) -> str:
        """Format raw text for output
        
        Meant to be overridden in subclasses
        
        Args:
            raw: the raw text to format
        """
        raise NotImplementedError
    
    def _pre_format(self, the_text: str) -> str:
        """Do pre formatting steps before calling the main format function
        
        Args:
            the_text: the text to format
        
        Returns:
            the formatted text
        """        
        the_text = the_text.lower()
        the_text = the_text.strip()
        return the_text
    
    def replace_fixed_patterns(self, the_text: str) -> str:
        """replace fixed text patterns with desired text
        
        Hunts through the text for certain patterns, and replaces with desired patterns
        
        Args:
            the_text: the text to format
        
        Returns:
            the formatted text
        """
        for orig, replace in self._fixed_replace_patterns.items():
            the_text = the_text.replace(orig, replace)
        return the_text

    def fix_closures(self, input_text) -> str: # pylint: disable=too-many-branches
        """Fix formatting of closures, or text surrounded by the relevant special character, e.g. `asdf`
        
        Args:
            input_text: the text to format

        Returns:
            the formatted text
        """
        output_chars = []

        # state machines for handling open / close state of special 
        # characters. if the state is true, that means the next one of these
        # characters is the opening of a closure . if false, the next
        # character is an end of closure.
        state_backtick_open = True
        # double quote
        state_d_quote_open = True
        # single quote
        state_s_quote_open = True
        # state_paren_open = True

        # array of indices of white spaces to be removed
        remove_whitespace_indcs = []
        for ichar, char in enumerate(input_text):            
            if char == '`':
                if state_backtick_open:
                    # remove the following white space, if any
                    remove_whitespace_indcs.append(ichar + 1)
                    state_backtick_open = False
                else:
                    # remove the preceding whitespace, if any
                    remove_whitespace_indcs.append(ichar - 1)
                    state_backtick_open = True
            if char == '"':
                if state_d_quote_open:
                    remove_whitespace_indcs.append(ichar + 1)
                    state_d_quote_open = False
                else:
                    remove_whitespace_indcs.append(ichar - 1)
                    state_d_quote_open = True
            if char == "'":
                if state_s_quote_open:
                    remove_whitespace_indcs.append(ichar + 1)
                    state_s_quote_open = False
                else:
                    remove_whitespace_indcs.append(ichar - 1)
                    state_s_quote_open = True
            if char == '(':
                if self._remove_space_before_open_paren:
                    remove_whitespace_indcs.append(ichar - 1)
                remove_whitespace_indcs.append(ichar + 1)
            if char == ')':
                remove_whitespace_indcs.append(ichar - 1)
                if self._remove_space_after_close_paren:
                    remove_whitespace_indcs.append(ichar + 1)

        output_chars = []
        for ichar, char in enumerate(input_text):
            # add back in chars that are not meant to be removed
            if ichar not in remove_whitespace_indcs:
                # no op, we don't add it
                output_chars.append(char)
            # but wait, if it's not whitespace, then it should't be removed
            elif char != ' ':
                output_chars.append(char)
            # all other stuff gets removed

        return ''.join(output_chars)


class PlainTextFormatter(TextFormatter):
    """Formatter for plaintext, long-form output
    """
    def __init__(self):
        super().__init__()
        
        # did we see an end of sentence at the end of the last utterance?
        self._saw_end_of_sentence = False
        # number words that have been written out
        self._count_words_out = 0

        # should set this to true if the user took some action before 
        # the next utterance
        self.next_iter_saw_user_action = False
        # should set this to true if want to force capitalization for next utterance
        self.next_iter_force_capitalize = False

        # want padding around ()
        # actually, just set these to true for now
        self._remove_space_before_open_paren = True
        self._remove_space_after_close_paren = True

    def format(self, raw: str) -> str:
        """See superclass docs"""
        the_text = self._pre_format(raw)
        self._log_step(1, the_text)

        logger.debug("Saw mouse_clicked: %s", str(event_mngr.mouse_clicked.is_set()))
        logger.debug("Saw mouse_doubleclicked: %s", str(event_mngr.mouse_doubleclicked.is_set()))
        logger.debug("Saw key_pressed: %s", str(event_mngr.key_pressed.is_set()))
        logger.debug("Saw manual sentence end: %s", str(event_mngr.saw_manual_sentence_end.is_set()))
        
        # check if there was a user action since last time 
        saw_user_action = event_mngr.mouse_clicked.is_set() or \
            event_mngr.key_pressed.is_set()
        saw_doubleclick = event_mngr.mouse_doubleclicked.is_set()
        # check if we should force capitalization
        force_capitalize = event_mngr.saw_manual_sentence_end.is_set()

        # capitalize the text after we see a double click
        if saw_doubleclick:
            force_capitalize = True

        if saw_user_action:
            self._saw_end_of_sentence = False
        
        last_char = the_text[-1:]
        
        ## Handle spaces 1: identify (don't add yet)

        # explicitly mark that we need to add a space, if "space bar" 
        # precedes everything else
        explicit_space_add = False
        if the_text[:10] in ['space bar ']:
            the_text = the_text[10:]
            explicit_space_add = True
        if the_text[:9] in ['spacebar ']:
            the_text = the_text[9:]
            explicit_space_add = True
        self._log_step(2, the_text)

        ## very hacky, the hijacking of "a m" as "a.m." bothers me
        the_text = the_text.replace('a.m.', 'a m')
        self._log_step(3, the_text)


        ## Compress repeated single letters into a single token (so that 
        # multiple letters can be dictated easily for an acronym )
        # note it's fine to do this right now because we haven't added any 
        # spaces yet
        tokens = the_text.split()
        out_tokens = []
        current_token = ""
        for token in tokens:
            if len(token) == 1 and (token.isdigit() or token.isalpha()):
                # build up token from partials
                current_token += token
            else:
                # if we were previously building up a token from partials, 
                # now we're stopping. We should add it.
                if len(current_token) > 0:
                    out_tokens.append(current_token)
                current_token = token
                out_tokens.append(current_token)
                current_token = ""
        # handle the case where we were building up from partials until 
        # the end of text
        if len(current_token) > 0:
            out_tokens.append(current_token)
        the_text = ' '.join(out_tokens)
        self._log_step(4, the_text)


        ## Handle triggered capitalization 
        the_text = the_text.replace('all caps', 'allcaps')
        tokens = the_text.split()
        # make this into a single token so it's easier to work with
        out_tokens = []
        next_capitalize = False
        next_all_caps = False
        for token in tokens:
            # note the below are escape words and can't be used regularly
            if token in ['capital','capitol']:
                next_capitalize = True
            elif token == 'allcaps':
                next_all_caps = True
            elif next_capitalize:
                out_tokens.append(token.capitalize())
                next_capitalize = False
            elif next_all_caps:
                out_tokens.append(token.upper())
                next_all_caps = False
            else:
                out_tokens.append(token)
        the_text = ' '.join(out_tokens)
        self._log_step(5, the_text)
        
        ## Handle triggered camel/pascal case
        # new chimney variable chimney name -> newVariableName
        tokens = the_text.split()
        # make this into a single token so it's easier to work with
        out_tokens = []
        next_camel = False
        next_all_caps = False
        for token in tokens:
            # note the below are escape words and can't be used regularly
            if token in ['chimney', 'jimmy', 'timmy']:
                next_camel = True
            elif next_camel:
                # append capitalized token onto the last token
                if len(out_tokens) > 0:
                    out_tokens[-1] += token.capitalize()
                else:
                    out_tokens.append(token.capitalize())
                next_camel = False
            else:
                out_tokens.append(token)
        the_text = ' '.join(out_tokens)
        self._log_step(6, the_text)


        ## Handle automatic capitalization
        # Only do this if we saw the end of a sentence
        if self._saw_end_of_sentence or force_capitalize:
            the_text = the_text.capitalize()
        self._log_step(7, the_text)

        
        ## Capitalize second, third, fourth ... sentences
        # todo: should only do this when in long-form text mode, it tramples on dot notation in python
        # not the most efficient code, but whatever
        # for char in END_OF_SENTENCE_CHARS:
        #     # make all end of sentence characters be separate tokens, so they can be split
        #     # i.e. , replace "." with " ."
        #     the_text = the_text.replace(char, ' '+char)
        # tokens = the_text.split()
        # # make this into a single token so it's easier to work with
        # out_tokens = []
        # next_cap = False
        # for token in tokens:
        #     # if we found a period, we need to capitalize the next word
        #     if token in END_OF_SENTENCE_CHARS:
        #         next_cap = True
        #         out_tokens.append(token)
        #     elif next_cap:
        #         # append capitalized token onto the last token
        #         out_tokens.append(token.capitalize())
        #         next_cap = False
        #     else:
        #         out_tokens.append(token)
        # the_text = ' '.join(out_tokens)
        # for char in END_OF_SENTENCE_CHARS:
        #     the_text = the_text.replace(' '+char, char)
        # self._log_step(8, the_text)


        ## Handle spaces 2: Add
        # There should be a leading space if:
        # - There was no user action such that we're "typing in a new place", 
        # - The text is more than one character long.
        # - There's an explicit space add
        if (not saw_user_action and len(the_text) > 1) or explicit_space_add:
            the_text = " " + the_text
        self._log_step(9, the_text)
        
        # check if currently the end of sentence
        if last_char in END_OF_SENTENCE_CHARS:
            self._saw_end_of_sentence = True
        else:
            self._saw_end_of_sentence = False
        self._log_step(10, the_text)

        the_text = self.replace_fixed_patterns(the_text)
        self._log_step(11, the_text)
        
        the_text = self.fix_closures(the_text)
        self._log_step(12, the_text)

        return the_text

class CodeTextFormatter(TextFormatter):
    """Formatter for code"""

    def __init__(self):
        super().__init__()
        # no padding around ()
        self._remove_space_before_open_paren = True
        self._remove_space_after_close_paren = True

    def format(self, raw: str) -> str:
        """See superclass docs"""
        # currently unimplemented
        pass
    