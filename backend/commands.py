# pylint: disable=arguments-differ

from __future__ import annotations
from copy import copy, deepcopy
import logging
import time
from typing import List, Dict, Any, Tuple, Optional

from pynput.keyboard import Controller, Key

from backend.keystrokes import execute_modified_keystroke
from backend.actions import Action, ActionHistory
from ui.kb_controller import KBCntrlrWrapper

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# the separator used between separate keys within a hotkey, e.g. 'ctrl+a'
HOTKEY_SEPARATOR = '+'

# use , to delimit multiple commands
MULTIPLE_COMMAND_DELIMITER = ', '

class CommandMultiplierParser:
    """Handles the parsing of command multiplier strings

    Command multiplier strings are used to specify the number of times that a command must be executed. Examples: '3 times', '4 x'
    """

    # all the different tokens that can be used for a multiplier post fix
    # note that the multiplier postfix is optional note.
    postfixes = ['*', 'times', 'times', 'x', 'X']

    # hard-coded conversions from tokens to numbers. Accounts for edge
    # cases we've seen
    multiplier_fixed_conversions = {
        'to': 2,
        'two': 2,
        'double': 2,
        'three': 3,
        'triple': 3,
        'for': 4,
        'quadruple': 4,
        'five': 5,
    }

    @staticmethod
    def check_valid_multiplier_token(token: str):
        """Returns true if the string token could be interpreted as a command multiplier token

        This is useful for checking if a command name would clash with a command multiplier string

        Args:
            token: the string to check for validity

        Returns:
            True if the token could be a multiplier token
        """

        ## is it valid as the first number token in a command multiplier?
        try:
            int(token)
            # it's an integer, therefore it is a valid multiplier token
            return True
        except ValueError:
            # it's not an integer
            pass

        if token in CommandMultiplierParser.multiplier_fixed_conversions.keys():
            return True

        ## is it valid as the multiplier postfix in a command multiplier?
        if token in CommandMultiplierParser.postfixes:
            return True

        return False

    @staticmethod
    def convert_multiplier(token: str) -> Optional[int]:
        """Convert a command multiplier token into the actual number

        Args:
            token: the token from the raw command

        Returns:
            the converted multiplier, or None if it couldn't be converted
        """

        # first see if it's an integer
        try:
            cmd_multiplier = int(token)
        # if we don't find a number here, then see if it's in the fixed
        # conversions dictionary
        except ValueError:
            cmd_multiplier = CommandMultiplierParser.multiplier_fixed_conversions.get(token, None)
        return cmd_multiplier

    @staticmethod
    def parse_multiplier_string(
            multiplier_string: str) -> Tuple[int, int]:
        """Determines the multiplier number from a raw multiplier string

        Args:
            multiplier_string: the most player string, see class
                documentation for examples

        Returns:
            Tuple of:
            - the multiplier number
            - the number of tokens used from the multiplier string to parse
                the multiplier number. This is useful if the input multiplier
                string could have trailing tokens that are not actual
                multiplier string tokens
        """

        tokens_used = 0

        tokens = multiplier_string.split()

        ## look for the multiplier number
        cmd_multiplier = CommandMultiplierParser.convert_multiplier(
            tokens[0])
        # if a valid multiplier was not found, the multiplier is
        # implicitly 1
        if cmd_multiplier is None:
            cmd_multiplier = 1
            return cmd_multiplier, tokens_used
        else:
            tokens_used += 1

        ## look for the multiplier postfix

        if tokens[1] in CommandMultiplierParser.postfixes:
            tokens_used += 1

        return cmd_multiplier, tokens_used


# forward declare this so it can be used in
class CommandRegistry:
    """see implementation below"""
    pass

class CommandExecutor(Action):
    """Executes a command

    Meant to be subclassed for specific command types
    """
    def __init__(self, cmd_reg: CommandRegistry):
        """Init

        Args:
            cmd_reg: command registry, for command lookup
        """
        self.cmd_reg = cmd_reg

    def execute(self,
            action_history: ActionHistory,
            cmd_execution_state: Dict[str, Any],
            stt_args: Optional[str] = None,):
        """Execute the command, with given arguments

        should be overridden in subclasses

        Args:
            action_history:  the history of actions executed. Used by some
                commands
            stt_args: string of additional arguments received for an
                individual command
            cmd_execution_state: dictionary of bespoke state to pass to
                command executors

        Returns:
            an action for action history
        """
        raise NotImplementedError

    def safe_deepcopy(self) -> CommandExecutor:
        """Deep copy this object, without copying things that shouldn't be copied

        Returns:
            a new copy
        """
        new_copy = copy(self)
        for name, val in self.__dict__.items():
            # skip cmd_reg, because it has a thread lock in it
            if name in ['_kb_controller', 'cmd_reg']:
                continue
            # others, deepcopy, to make sure there's no crosstalk between instances
            else:
                self.__dict__[name] = deepcopy(val)
        return new_copy



class KeystrokeCmdExec(CommandExecutor):
    """Execute a keystroke command, which is a series of 1 or more hotkeys

    Command name: 'keystroke'
    cmd_def_kwargs:
        'keys':
            list of sequential keystroke hotkeys to execute, where each
            hotkey may be one regular key plus 0 or more modifiers.

            Can also include "delay <float time>" to specify insertion of a delay

            Example: ['ctrl-c','delay 0.25','alt-v','tab','enter']
    """

    def __init__(self, cmd_reg: CommandRegistry,
            kb_controller: KBCntrlrWrapper,
            keys: List[str],
            prepend_whitespace_when_embedded: bool = False):
        """Init

        Args:
            kb_controller: the keyboard controller for doing kb output
            keys: see class docs
        """
        super().__init__(cmd_reg)
        self.keys = keys
        self._kb_controller = kb_controller
        self.hotkey_separator = HOTKEY_SEPARATOR

        self.prepend_whitespace = prepend_whitespace_when_embedded

    def execute(self,
            action_history: ActionHistory,
            cmd_execution_state: Dict[str, Any],
            stt_args: Optional[str] = None):
        """Execute command

        Note that when using system hotkeys like super+tab, you may need to
        insert a delay afterwards

        Args:
            action_history: see superclass
            cmd_execution_state: see superclass
            stt_args: see superclass
        """
        logger.debug("KeystrokeCmdExec: typing keys: '{}'".format(self.keys))

        embedded_command = cmd_execution_state['embedded_command']

        # there should be no speech to text arguments for keystroke command
        assert stt_args is None

        # type a space if desired
        if self.prepend_whitespace and embedded_command:
            self._kb_controller.tap(Key.space)

        for hotkey in self.keys:
            # deal with delay
            if hotkey.startswith('delay'):
                delay_time = float(hotkey.split()[1])
                time.sleep(delay_time)
                continue

            execute_modified_keystroke(self._kb_controller, hotkey, self.hotkey_separator)

    # def undo(self) -> bool:
    #     """Undo the action

    #     Returns:
    #         True if this undo was "substantial". See documentation for
    #             Action() for more information
    #     """
    #     return True


class TypeCmdExec(CommandExecutor):
    """Execute a type command, which is just typing out a string

    Command name: 'type'
    cmd_def_kwargs:
        'content': the string content to type, e.g. "I'm a string"
    """

    def __init__(self, cmd_reg: CommandRegistry,
            kb_controller: KBCntrlrWrapper,
            content: List[str],
            prepend_whitespace_when_embedded: bool = True
            ):
        """Init

        Args:
            content: see class docs
        """
        super().__init__(cmd_reg)
        self.text = content
        self._kb_controller = kb_controller

        self.prepend_whitespace = prepend_whitespace_when_embedded

    def execute(self,
            action_history: ActionHistory,
            cmd_execution_state: Dict[str, Any],
            stt_args: Optional[str] = None):
        """Execute command

        Args:
            action_history: see superclass
            cmd_execution_state: see superclass
            stt_args: see superclass
        """
        embedded_command = cmd_execution_state['embedded_command']

        if self.prepend_whitespace and embedded_command:
            self.text = ' ' + self.text

        logger.debug("TypeCmdExec: typing: '{}'".format(self.text))

        # there should be no speech to text arguments for keystroke command
        assert stt_args is None

        self._kb_controller.type(self.text)

    def undo(self) -> bool:
        """Undo the text writing action

        Deletes all the characters written

        Returns:
            True, because this action is "substantial". See
                documentation for Action() for more information
        """
        logger.debug('TypeCmdExec: undo, deleting text {}'.format(self.text))
        for char in self.text: #pylint: disable=unused-variable
            self._kb_controller.tap(Key.backspace)
        return True

class CaseCmdExec(CommandExecutor):
    """Executea case command, which formats the text arguments with a specific case, like snake case

    Command name: 'case'
    cmd_def_kwargs:
        'case': the case to use
        'in_place': if true, will apply the case to the highlighted text

    Cases:
        upper: SLIM SHADY
        lower: slim shady
        title: Slim Shady
        snake: slim_shady
        screaming snake: SLIM_SHADY
        camel: slimShady
    """

    CASES = [
        'upper',
        'lower',
        'title',
        'snake',
        'screaming snake',
        'camel',
        'pascal',
        'lower letters',
        'upper letters'
        'name letters'
    ]

    def __init__(self, cmd_reg: CommandRegistry,
            kb_controller: KBCntrlrWrapper,
            case: str,
            in_place: bool,
            prepend_whitespace_when_embedded: bool = True
            ):
        """Init

        Args:
            cmd_reg: see superclass docs
            case: see class docs
            in_place: see class docs
        """
        super().__init__(cmd_reg)
        self.case = case
        # todo
        if in_place:
            raise NotImplementedError
        self.in_place = in_place

        self._kb_controller = kb_controller

        # whether or not to prepend and append a white space before / after the formatted text
        self.prepend_whitespace = prepend_whitespace_when_embedded
        # self.append_whitespace = False

    def execute(self,
            action_history: ActionHistory,
            cmd_execution_state: Dict[str, Any],
            stt_args: Optional[str] = None):
        """Execute command

        Args:
            action_history: see superclass
            cmd_execution_state: see superclass
            stt_args: see superclass
        """
        embedded_command = cmd_execution_state['embedded_command']

        if not self.in_place:
            the_text = CaseCmdExec.format_case(stt_args, self.case)
            if self.prepend_whitespace and embedded_command:
                the_text = ' ' + the_text
            # if self.append_whitespace:
            #     the_text = the_text + ' '
            logger.debug("CaseCmdExec: typing: '{}'".format(the_text))
            self.text = the_text
            self._kb_controller.type(the_text)
        else:
            # there should be no speech to text arguments for this case
            assert stt_args is None

    def undo(self) -> bool:
        """Undo the text writing action

        Deletes all the characters written

        Returns:
            True, because this action is "substantial". See
                documentation for Action() for more information
        """
        logger.debug('CaseCmdExec: undo, deleting text {}'.format(self.text))
        for char in self.text: #pylint: disable=unused-variable
            self._kb_controller.tap(Key.backspace)
        return True

    @staticmethod
    def format_case(text: str, case: str) -> str: #pylint: disable=too-many-return-statements
        """Format a list of string tokens in the given case

        Args:
            text: string of words separated by spaces
            case: the case in which to format

        Returns:
            the formatted string
        """
        tokens = text.split()
        # the raw tokens look like: 'bay laugh anguish hannover'
        # returns 'BAY LAUGH ANGUISH HANNOVER'
        if case == 'upper':
            return ' '.join([token.upper() for token in tokens])

        # the raw tokens look like: 'bay laugh anguish hannover'
        # returns 'bay laugh anguish hannover'
        elif case == 'lower':
            return ' '.join([token.lower() for token in tokens])

        # the raw tokens look like: 'bay laugh anguish hannover'
        # returns 'Bay Laugh Anguish Hannover'
        elif case == 'title':
            return ' '.join([token.capitalize() for token in tokens])

        # the raw tokens look like: 'bay laugh anguish hannover'
        # returns 'BayLaughAnguishHannover'
        elif case == 'pascal':
            return ''.join([token.capitalize() for token in tokens])

        # the raw tokens look like: 'bay laugh anguish hannover'
        # returns 'bay_laugh_anguish_hannover'
        elif case == 'snake':
            return '_'.join(tokens)

        # the raw tokens look like: 'bay laugh anguish hannover'
        # returns 'BAY_LAUGH_ANGUISH_HANNOVER'
        elif case == 'screaming snake':
            return '_'.join([token.upper() for token in tokens])

        # the raw tokens look like: 'bay laugh anguish hannover'
        # returns 'bayLaughAnguishHannover'
        elif case == 'camel':
            return ''.join(
                [tokens[0].lower()] + [token.capitalize() for token in tokens[1:]])

        # the raw tokens look like: 'bay laugh anguish hannover'
        # returns 'BLAH'
        elif case == 'acronym':
            first_letters = [token[0].upper() for token in tokens]
            return ''.join(first_letters)

        # the raw tokens look like: 'blah' or 'b l a h'
        # returns 'blah'
        elif case == 'lower letters':
            joined = ''.join(tokens)
            joined = joined.replace(' ','')
            return joined.lower()

        # the raw tokens look like: 'blah' or 'b l a h'
        # returns 'BLAH'
        elif case == 'upper letters':
            joined = ''.join(tokens)
            joined = joined.replace(' ','')
            return joined.upper()

        # the raw tokens look like: 'blah' or 'b l a h'
        # returns 'Blah'
        elif case == 'name letters':
            joined = ''.join(tokens)
            joined = joined.replace(' ','')
            return joined.capitalize()

        else:
            raise NotImplementedError

class SublimeFindCmdExec(CommandExecutor):
    """Execute a sublime find command to move to desired text within the current file

    Command name: 'sublime_find'
    cmd_def_kwargs:
        'direction': the direction in which to do the find, either forwards (down) or backwards (up)
    """

    def __init__(self, cmd_reg: CommandRegistry,
            kb_controller: KBCntrlrWrapper,
            direction: str, find_hotkey: str = 'ctrl+f'):
        """Init

        Args:
            cmd_reg: see superclass docs
            direction: see class docs
        """
        super().__init__(cmd_reg)
        self.direction = direction
        self._kb_controller = kb_controller
        self.hotkey_separator = HOTKEY_SEPARATOR
        self.find_hotkey = find_hotkey

    def execute(self,
            action_history: ActionHistory,
            cmd_execution_state: Dict[str, Any],
            stt_args: Optional[str] = None):
        """Execute command

        Args:
            action_history: see superclass
            cmd_execution_state: see superclass
            stt_args: see superclass
        """

        if not stt_args:
            logger.debug("SublimeFindCmdExec: found no string to search for")

        multiplier_separator_substr = ' pipe '

        # the expected format is "<string content to search><multiplier_separator_substr><multiplier string>", where  multiplier format is per CommandMultiplierParser
        try:
            content, multiplier_str = stt_args.split(multiplier_separator_substr)

            #
            cmd_multiplier, _ = CommandMultiplierParser.parse_multiplier_string(multiplier_str)
            num_tabs = cmd_multiplier

        except ValueError:
            # in this case, make sure that there's not a semicolon in the string at all (the value error could be because there were multiple semicolons, which is unexpected in current implementation)
            assert stt_args.find(multiplier_separator_substr) == -1

            # just assume the whole thing is content in this case
            content = stt_args
            num_tabs = 0

        logger.debug("SublimeFindCmdExec: searching for '{}', tabbing {} times".format(content, num_tabs))

        # enter the find dialog in sublime text
        execute_modified_keystroke(self._kb_controller, self.find_hotkey, self.hotkey_separator)

        #throw in a sleep, because if I try to use this in the browser not all the content gets captured
        time.sleep(0.2)

        # type the search string
        self._kb_controller.type(content)

        for icommand in range(num_tabs):
            self._kb_controller.tap(Key.tab)

        # hit enter to drop the cursor to the left of the search string
        self._kb_controller.tap(Key.enter)

    def undo(self) -> bool:
        """Undo

        Returns:
            False, because this action is not considered "substantial". See
                documentation for Action() for more information
        """
        # note that this is a noop
        return False

class UndoUtteranceCmdExec(CommandExecutor):
    """Undo the last utterance

    Command name: 'undo_utterance'
    cmd_def_kwargs:
        None
    """

    def __init__(self, cmd_reg: CommandRegistry,
                 kb_controller: KBCntrlrWrapper):
        """Init

        Args:
            cmd_reg: see superclass docs
            direction: see class docs
        """
        super().__init__(cmd_reg)

    def execute(self,
            action_history: ActionHistory,
            cmd_execution_state: Dict[str, Any],
            stt_args: Optional[str] = None):
        """Execute command

        Args:
            action_history: see superclass
            cmd_execution_state: see superclass
            stt_args: see superclass
        """

        assert stt_args is None

        logger.debug("UndoUtteranceCmdExec: undoing last utterance")

        # undo the utterance
        substantial = action_history.undo_utterance()
        # if the actions in an utterance are considered "not substantial", this
        # will be False. In that case, we should proceed to continue undoing
        # until we reach a substantial undo
        while not substantial:
            substantial = action_history.undo_utterance()

    def undo(self) -> bool:
        """Undo

        Returns:
            False, because this action is not considered "substantial". See
                documentation for Action() for more information
        """
        # note that this is a noop - we're not going to revert the undoing
        # action
        return False

class ChainCommandExec(CommandExecutor):
    """Execute a chain command, which is multiple commands strung together

    Command name: 'chain'
    cmd_def_kwargs:
        'commands': a list of command names to execute, in order
    """

    def __init__(self, cmd_reg: CommandRegistry, 
            kb_controller: KBCntrlrWrapper,
            commands: List[str]):
        """Init

        Args:
            commands: see class docs
        """
        super().__init__(cmd_reg)
        self.commands = commands
        self.executed_actions: List[Action] = []

    def execute(self,
            action_history: ActionHistory,
            cmd_execution_state: Dict[str, Any],
            stt_args: Optional[str] = None):
        """Execute command

        Args:
            action_history: see superclass
            cmd_execution_state: see superclass
            stt_args: see superclass

        Returns:
            the actions taken
        """

        # there should be no speech to text arguments for chain command
        assert stt_args is None

        for icommand, cmd_name in enumerate(self.commands):
            executor = self.cmd_reg.get_command_executor(cmd_name)
            # cmd_def_kwargs = self.cmd_reg.get_command_def_kwargs(cmd_name)

            # if we are in a chain, this should only be true for the first one
            if icommand > 0:
                cmd_execution_state['embedded_command'] = False

            self.executed_actions.append(
                executor.execute(action_history,
                    cmd_execution_state, stt_args=None))

    def undo(self) -> bool:
        """Undo

        Returns:
            True, if all the actions in this chain are "substantial". See
                documentation for Action() for more information
        """
        substantial = False
        for action in self.executed_actions:
            # if any of the actions was considered substantial, the whole utterance is substantial
            new_substantial = action.undo()
            substantial = substantial or new_substantial
        return substantial

CommandDefinition = Dict[str, Any]
CommandDefinitionKwargs = Dict[str, Any]

# disabling function redefined because we need this class defined for chain command exec
class CommandRegistry: # pylint: disable=function-redefined
    """Maintains a registry of all the known commands
    """

    # nothing from string command type in the command definition to the class
    command_types = {
        'keystroke': KeystrokeCmdExec,
        'chain': ChainCommandExec,
        'type': TypeCmdExec,
        'case': CaseCmdExec,
        'sublime_find': SublimeFindCmdExec,
        'undo_utterance': UndoUtteranceCmdExec,
    }

    def __init__(self, commands_def: List[CommandDefinition], kb_controller: KBCntrlrWrapper):
        """Init

        Args:
            commands_def: the commands definition, loaded from file or elsewhere
        """

        # the mapping
        # dictionary mapping command name to command executor
        # self.commands: Dict[str, CommandExecutor] = None

        # mapping from a command name to the executor instance for it
        self.commands: Dict[str, CommandExecutor] = {}

        # have to store this so it can be passed to all underlying commands
        self.kb_controller = kb_controller

        # tree of nested dicts encoding a lookup table for command name tokens, like:
        # first word      second word      third word
        # do          ->  my           ->  homework
        #                              ->  chores
        #             ->  his          ->  makeup
        # watch       ->  tv           ->  (none)
        #             ->  netflix      ->  tonight
        #
        # note this tree is kinda memory heavy, but whatevs. We only need one, and lookup is fast for Dicts
        # real life test: for 42 commands this took up 2272 bytes
        self._cmd_token_tree = {}

        self.update_commands(commands_def)

    def update_commands(self, commands_def: List[CommandDefinition]):
        """Update the commands in the internal registry

        Args:
            commands_def: the commands definition, loaded from file or elsewhere
        """
        # clear all these first
        self.commands = {}

        for icommand, command_def in enumerate(commands_def):
            kwargs = command_def['kwargs']
            all_names = [command_def['name']] + command_def.get('aliases', [])
            for name in all_names:
                logger.debug('(%d) Loading command: %s', icommand, name)
                self.commands[name] = \
                    self.command_types[command_def['command_type']](
                        self, kb_controller=self.kb_controller, **kwargs)

        self._build_cmd_token_tree()

    @property
    def cmd_names(self) -> List[str]:
        """Returns a list of command names

        Returns:
            the command names
        """
        return list(self.commands.keys())

    def _build_cmd_token_tree(self):
        """Build internal look up table of command words
        """

        # reset it
        self._cmd_token_tree = {}

        for cmd_name in self.cmd_names:
            words = cmd_name.split()
            first_word = words[0]
            # command names should have no conflicts with command multiplier tokens
            cmd_name_invalid = CommandMultiplierParser.check_valid_multiplier_token(first_word)
            if cmd_name_invalid:
                raise ValueError(f'Token "{first_word}" is not a valid beginning of a command name. It could be interpreted as a command multiplier')

            # todo: add support for more than 3 levels?
            current_level = self._cmd_token_tree
            current_level.setdefault(words[0], {})
            current_level = self._cmd_token_tree[words[0]]
            if len(words) > 1:
                current_level.setdefault(words[1], {})
                current_level = current_level[words[1]]
            if len(words) > 2:
                # IT ENDS HERE!
                current_level.setdefault(words[2], {})
            if len(words) > 3:
                raise NotImplementedError

    def cmd_name_next_tokens(self, tokens_so_far: List[str]) -> List[str]:
        """Get the available tokens in the next slot for a command name


        Args:
            tokens_so_far: list of tokens that have been parsed from the
                command name thus far. Eg, if the command name is "do my
                homework", then ['do'] would return ['my'] (and
                additional tokens, if other commands start with 'do')

        Returns:
            list of next available words for valid command names
        """

        current_level = self._cmd_token_tree
        next_tokens = current_level.keys()
        for token in tokens_so_far:
            try:
                current_level = current_level[token]
                next_tokens = current_level.keys()
            except KeyError:
                #pylint: disable=raise-missing-from
                raise ValueError(
                    f'No command found with tokens {tokens_so_far}')
                #pylint: enable=raise-missing-from
        return list(next_tokens)

    def get_command_executor(self, cmd_name: str) -> CommandExecutor:
        """Get the executor instance for a given command name

        Args:
            cmd_name: the name of the command

        Returns:
            executor instance
        """
        # make a deep copy before returning, because each CommandExecutor keeps
        # track of a single instance of executing a command
        return self.commands[cmd_name].safe_deepcopy()

class CommandDispatcher:
    """Handles the execution of all single commands

    Parses and executes the text for any command. delegates the details of
    execution to subclasses of CommandExecutor.
    """

    def __init__(self, cmd_reg: CommandRegistry, action_history: ActionHistory):
        """Init

        Args:
            cmd_reg: the command
        """
        self.cmd_reg = cmd_reg
        self.action_history = action_history

    def dispatch(self, raw_command_text: str,
            cmd_execution_state: Dict[str, Any]) -> List[Action]:
        """Dispatch a given raw command text for execution

        Args:
            raw_command_text: the raw string command text, as output by the
                speech-to-text engine
            cmd_execution_state: dictionary of bespoke state to pass to
                command executors

        Returns:
            the actions taken
        """

        logger.debug("Raw command: '{}'".format(raw_command_text))

        # if there are multiple commands, we should split them out
        commands = raw_command_text.split(MULTIPLE_COMMAND_DELIMITER)

        # the actions taken by the commands
        actions = []

        for icommand, command in enumerate(commands):
            cmd_name, cmd_mult, cmd_args = self.parse(command)

            logger.debug("  Raw command {}: '{}'".format(icommand, command))
            logger.debug("  Command name: '{}'".format(cmd_name))
            logger.debug("  embedded_command: {}".format(cmd_execution_state['embedded_command']))

            executor = self.cmd_reg.get_command_executor(cmd_name)

            # execute cmd_mult times
            for _ in range(cmd_mult):
                executor.execute(self.action_history,
                    cmd_execution_state=cmd_execution_state,
                    stt_args=cmd_args
                    )
                # here, the executor IS the action
                actions.append(executor)

        return actions

    def parse(self, command_text: str) -> Tuple[str, int, str]: #pylint: disable=too-many-branches
        """Parse a command text

        Rurns a raw command string into arguments for actual execution

        Args:
            command_text: the raw string command text, as output by the
                speech-to-text engine

        Returns:
            Tuple the command name, the execution multiplier, and remaining argument text for
                the command
        """
        tokens = command_text.split(' ')

        # extracted command characteristics
        cmd_name_tokens = []
        cmd_multiplier = None
        cmd_args = None

        # first, let's try parsing the command multiplier at the beginning of the string
        # tokens_used tells us how many of the tokens were actually in the command multiplier. If there is no multiplier (implicit 1), then tokens used will be zero
        cmd_multiplier, tokens_used = CommandMultiplierParser.parse_multiplier_string(' '.join(tokens[:2]))

        tokens = tokens[tokens_used:]

        # state machine for parsing the rest of the command name and the args
        state = 'command_name_0'
        itoken = 0
        while state != 'done' and itoken < len(tokens):
            token = tokens[itoken]
            # first word in the command name
            if state == 'command_name_0':
                # see if the token is a known first word
                if token in self.cmd_reg.cmd_name_next_tokens(cmd_name_tokens):
                    cmd_name_tokens.append(token)
                    state = 'command_name_1'
                # there must be at least one expected word for it to be a real
                # command
                else:
                    raise Exception(f"Expected a known command name, found {token}")
            # second word in the command name (optional)
            elif state == 'command_name_1':
                # see if the token is a known second word
                if token in self.cmd_reg.cmd_name_next_tokens(cmd_name_tokens):
                    cmd_name_tokens.append(token)
                    state = 'command_name_2'
                # if there is no second word, we're in the command args now
                else:
                    state = 'args'
                    # go back a token because we're actually at the args
                    itoken -= 1
            # third word in the command name (optional)
            elif state == 'command_name_2':
                # see if the token is a known third word
                if token in self.cmd_reg.cmd_name_next_tokens(cmd_name_tokens):
                    cmd_name_tokens.append(token)
                    state = 'args'
                # if there is no third word, we're in the command args
                else:
                    state = 'args'
                    # go back a token because we're actually at the args now
                    itoken -= 1
            # args. there can be an arbitrary number
            elif state == 'args':
                if cmd_args is None:
                    cmd_args = []
                cmd_args.append(token)
                state = 'args'

            itoken += 1

        # it should be a known command
        cmd_name = ' '.join(cmd_name_tokens)
        assert cmd_name in self.cmd_reg.cmd_names

        if cmd_args:
            # join together the tokens and output as a full string
            cmd_args = ' '.join(cmd_args)

        return cmd_name, cmd_multiplier, cmd_args


# class CompoundCommandExecutive:
#     def __init__(self):
#         self.command_exe = CommandDispatcher()

#     def execute(self, text: str):
#         command_texts = text.split(',')
#         # execute each command in order
#         for text in command_texts:
#             self.command_exe.execute(text)

# if __name__ == "__main__":

#     import json
#     with open('example_commands.json', 'r') as f:
#         commands_def_in = json.load(f)
#     cmd_reg = CommandRegistry(commands_def_in)

#     cmd_exec = CommandDispatcher(cmd_reg)
#     # import ipdb
#     # ipdb.set_trace()
#     # cmd_exec.dispatch('12 times dash')
#     cmd_exec.dispatch('3 dog')
