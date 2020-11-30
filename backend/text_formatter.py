import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

END_OF_SENTENCE_CHARS = ['?','.','!']

class TextFormatter:
    def __init__(self):
        # what step we're on in the formatting process
        self._step = 0

    def _log_step(self, the_text):
        logger.debug("Step %d: '%s'", self._step, the_text)
        self._step += 1

    
    def format(self, raw: str) -> str:
        raise NotImplementedError
    
    def _pre_format(self, the_text: str) -> str:
        self._step = 0
        
        the_text = the_text
        the_text = the_text.lower()
        the_text = the_text.strip()
        self._log_step(the_text)

        return the_text
    
    def _post_format(self, the_text: str) -> str:
        raise NotImplementedError

    def replace_fixed_patterns(self, the_text: str) -> str:
        # replace specific patterns
        the_text = the_text.replace(" i ", " I ")
        the_text = the_text.replace("i've", "I've")
        the_text = the_text.replace("quote", '"')
        # for backticks
        the_text = the_text.replace("backslider", '`')
        the_text = the_text.replace("back slider", '`')
        # # replace "space" with " "
        # the_text = the_text.replace(" space ", ' ')
        self._log_step(the_text)
        return the_text


class PlainTextFormatter(TextFormatter):
    def __init__(self):
        
        # did we see an end of sentence at the end of the last utterance?
        self._saw_end_of_sentence = False
        # number words that have been written out
        self._count_words_out = 0

        # should set this to true if the user took some action before the next
        # utterance
        self.saw_user_action = False

    def format(self, raw: str) -> str:
        the_text = self._pre_format(raw)

        if self.saw_user_action:
            self._saw_end_of_sentence = False
        
        last_char = the_text[-1:]
        
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
        self._log_step(the_text)

        ## Handle capitalization

        # Capitalize, if it begins with "capital/capitol"
        if the_text[:8] in ['capital ', 'capitol ']:
            the_text = the_text[8:]
            the_text = the_text.capitalize()
        self._log_step(the_text)

        # Only do this automatic capitalization if we saw the end of a 
        # sentence
        if self._saw_end_of_sentence:
            the_text = the_text.capitalize()
        self._log_step(the_text)

        ## Handle spaces 2

        # There should be a leading space if:
        # - There was no user action such that we're "typing in a new place", 
        # - The text is more than one character long.
        # - There's an explicit space add
        if (not self.saw_user_action and len(the_text) > 1) or explicit_space_add:
            the_text = " " + the_text
        self._log_step(the_text)
        
        # check if currently the end of sentence
        if last_char in END_OF_SENTENCE_CHARS:
            self._saw_end_of_sentence = True
        else:
            self._saw_end_of_sentence = False
        self._log_step(the_text)

        return the_text

class CodeTextFormatter(TextFormatter):
    def fix_closures(self, input_text) -> str:
        output_chars = []

        # state machines for handling open / close state of special 
        # characters. if the state is true, that means the next one of these
        # characters is the opening of a closure . if false, the next
        # character is an end of closure. A closure is text surrounded by the
        # relevant special character, e.g. ` asdf `
        state_backtick_open = True
        # double quote
        state_d_quote_open = True
        # single quote
        state_s_quote_open = True
        # state_paren_open = True

        # array of indices of white spaces to be removed
        remove_whitespace_indcs = []
        # last_char = None
        # next_char = None
        for ichar, char in enumerate(input_text):
            if ichar == len(input_text) - 1:
                next_char = None
            else:
                next_char = input_text[ichar + 1]
            
            # deal with white spaces
            # if char == ' ':
            #     if not remove_next_whitespace:
            #         output_chars.append(char)
            #     remove_next_whitespace = False
            
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
                # remove the following white space, if any
                remove_whitespace_indcs.append(ichar + 1)
                remove_whitespace_indcs.append(ichar - 1)
            if char == ')':
                # remove the preceding whitespace, if any
                remove_whitespace_indcs.append(ichar - 1)
                remove_whitespace_indcs.append(ichar + 1)

            last_char = char

        output_chars = []
        for ichar, char in enumerate(input_text):
            if not ichar in remove_whitespace_indcs:
                output_chars.append(char)

        return ''.join(output_chars)

