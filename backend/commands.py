# pylint: disable=arguments-differ

from enum import Enum
import logging
import time
from typing import List, Dict, Any, Tuple, Optional

from pynput.keyboard import Controller, Key

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# a single controller for all command executors
keyboard_controller = Controller()

# forward declare this so it can be used in
class CommandRegistry:
    """see implementation below"""
    pass

class CommandExecutor:
    """Executes a command
    
    Meant to be subclassed for specific command types    
    """
    def __init__(self, cmd_reg: CommandRegistry):
        """Init
        
        Args:
            cmd_reg: command registry, for command lookup
        """
        self.cmd_reg = cmd_reg

    def execute(self, stt_args: Optional[List[str]]):
        """Execute the command, with given arguments
        
        should be overridden in subclasses

        Args:
            stt_args: list of string arguments received from speech to text
        """
        raise NotImplementedError


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

    # the separator used between separate keys within a hotkey, e.g. 'ctrl+a'
    hotkey_separator = '+'
    modifiers_map = {
        'ctrl': Key.ctrl,
        'alt': Key.alt,
        'super': Key.cmd,
        'shift': Key.shift,
    }
    special_operand_keys = {
        'tab': Key.tab,
        'left': Key.left,
        'up': Key.up,
        'right': Key.right,
        'down': Key.down,
        'enter': Key.enter
    }

    def __init__(self, cmd_reg: CommandRegistry, keys: List[str]):
        """Init
                
        Args:
            keys: see class docs
        """
        super().__init__(cmd_reg)
        self.keys = keys
        self.keyboard_ctlr = keyboard_controller
        
        # hard-coded config parameters for now...
        # running this on a linux box
        self.is_linux = True
        # using sticky keys
        self.using_sticky_keys = True

    def parse_hotkey(self, hotkey: str) -> Tuple[List[Enum], str, bool]:
        """Parses a string specification for a hotkey into usable keys
        
        Given an input like 'ctrl-alt-a', returns a tuple of 
            (Key.ctrl, Key.alt, 'a'). Here, 'a' is the "operand" key.
        
        Args:
            hotkey: the hotkey string specifier
        
        Returns:
            a tuple of:
                - a list of modifiers Key.blah (the type of which is an Enum)
                - the string for the "operand" key.
                - a flag indicating if the key was a "special operand", i.e. one 
                    of the pyinput keys we have to explicitly map. This has
                    implications for later handling.
        """
        # todo: lru cache parse_hotkey()? kinda innefficient to run every time...

        hotkey_keys = hotkey.split(self.hotkey_separator)
        # modifiers should be at the front
        modifiers = hotkey_keys[:-1]
        operand_key = hotkey_keys[-1]
        
        # make sure they're all unique. we could end up with tricky bugs otherwise
        assert(len(modifiers)) == len(set(modifiers))
        modifiers_obj = [self.modifiers_map[mod] for mod in modifiers]

        assert operand_key not in self.modifiers_map
        # if there is a mapping in special operand keys, get it. otherwise
        # default to itself.
        if operand_key in self.special_operand_keys.keys():
            operand_key_mapped = self.special_operand_keys[operand_key]
            was_special_operand = True
        else:
            operand_key_mapped = operand_key
            was_special_operand = False
        return modifiers_obj, operand_key_mapped, was_special_operand

    def execute(self, stt_args: Optional[List[str]]):
        """Execute command

        Note that when using system hotkeys like super+tab, you may need to
        insert a delay afterwards
        
        Args:
            stt_args: see superclass
        """
        logger.debug("KeystrokeCmdExec: typing keys: '{}'".format(self.keys))

        # there should be no speech to text arguments for keystroke command
        assert stt_args is None
        for hotkey in self.keys:
            # deal with delay
            if hotkey.startswith('delay'):
                delay_time = float(hotkey.split()[1])
                time.sleep(delay_time)
                continue

            modifiers, operand_key, was_special_operand = self.parse_hotkey(hotkey)

            ## press the keys
            # see https://pynput.readthedocs.io/en/latest/keyboard.html
            # WARNING! does not work with sticky keys!
            # unfortunately I couldn't get this to work consistently with sticky
            # keys. Sometimes the modifiers are left engaged, other times not.
            # Behaviour is weird too with multiple modifier keys.
            
            if len(modifiers) > 0:
                last_modifier = modifiers[-1]
            with self.keyboard_ctlr.pressed(*modifiers):
                self.keyboard_ctlr.press(operand_key)
                self.keyboard_ctlr.release(operand_key)

            if self.is_linux and self.using_sticky_keys:
                ## Special handling for sticky keys...
                # if using sticky keys, pyinput explicits strange behavior from the
                # Xorg system...when using modifiers with non-special keys (like 
                # 'a', '6', or '~' whereas special would include Key.tab and Key.space)
                # not all of the modifiers will be cleared upon keypress of the 
                # operand_key. for whatever reason, the last modifier in the modifiers 
                # list won't be cleared.  we do that explicitly here.
                if len(modifiers) > 0 and not was_special_operand:
                    # we start out in sticky "single press" mode...cycle to 
                    # sticky latched
                    self.keyboard_ctlr.press(last_modifier)
                    self.keyboard_ctlr.release(last_modifier)
                    # now cycle to "unstuck"
                    self.keyboard_ctlr.press(last_modifier)
                    self.keyboard_ctlr.release(last_modifier)
    
class TypeCmdExec(CommandExecutor):
    """Execute a type command, which is just typing out a string
    
    Command name: 'type'
    cmd_def_kwargs: 
        'content': the string content to type, e.g. "I'm a string"
    """

    def __init__(self, cmd_reg: CommandRegistry, content: List[str]):
        """Init
        
        Args:
            content: see class docs
        """
        super().__init__(cmd_reg)
        self.content = content
        self.keyboard_ctlr = keyboard_controller
        
    def execute(self, stt_args: Optional[List[str]]):
        """Execute command
        
        Args:
            stt_args: see superclass
        """
        logger.debug("TypeCmdExec: typing: '{}'".format(self.content))

        # there should be no speech to text arguments for keystroke command
        assert stt_args is None
        self.keyboard_ctlr.type(self.content)
    
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

    CASES = ['upper', 'lower', 'title', 'snake', 'screaming snake', 'camel']

    def __init__(self, cmd_reg: CommandRegistry, case: str, in_place: bool):
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

        self.keyboard_ctlr = keyboard_controller
        
    def execute(self, stt_args: Optional[List[str]]):
        """Execute command
        
        Args:
            stt_args: see superclass
        """
        if not self.in_place:
            the_text = CaseCmdExec.format_case(
                ' '.join(stt_args), self.case)
            logger.debug("CaseCmdExec: typing: '{}'".format(the_text))
            self.keyboard_ctlr.type(the_text)
        else:
            # there should be no speech to text arguments for this case
            assert stt_args is None

    @staticmethod
    def format_case(text: str, case: str) -> str:
        """Format a list of string tokens in the given case
        
        Args:
            text: string of words separated by spaces
            case: the case in which to format

        Returns:
            the formatted string
        """
        tokens = text.split()
        if case == 'upper':
            return ' '.join([token.upper() for token in tokens])
        elif case == 'lower':
            return ' '.join([token.lower() for token in tokens])
        elif case == 'title':
            return ' '.join([token.capitalize() for token in tokens])
        elif case == 'snake':
            return '_'.join(tokens)
        elif case == 'screaming snake':
            return '_'.join([token.upper() for token in tokens])
        elif case == 'camel':
            return ''.join(
                [tokens[0].lower()] + [token.capitalize() for token in tokens[1:]])
        elif case == 'acronym':
            first_letters = [token[0].upper() for token in tokens]
            return ''.join(first_letters)
        else:
            raise NotImplementedError



class ChainCommandExec(CommandExecutor):
    """Execute a chain command, which is multiple commands strung together
    
    Command name: 'chain'
    cmd_def_kwargs: 
        'commands': a list of command names to execute, in order
    """

    def __init__(self, cmd_reg: CommandRegistry, commands: List[str]):
        """Init
        
        Args:
            commands: see class docs
        """
        super().__init__(cmd_reg)
        self.commands = commands

    def execute(self, stt_args: Optional[List[str]]):
        """Execute command
        
        Args:
            stt_args: see superclass
        """

        # there should be no speech to text arguments for chain command
        assert stt_args is None
        
        for cmd_name in self.commands:
            executor = self.cmd_reg.get_command_executor(cmd_name)        
            # cmd_def_kwargs = self.cmd_reg.get_command_def_kwargs(cmd_name)
            executor.execute(stt_args=None)

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
        'case': CaseCmdExec
    }

    def __init__(self, commands_def: List[CommandDefinition]):
        """Init
        
        Args:
            commands_def: the commands definition, loaded from file or elsewhere
        """

        # the mapping
        # dictionary mapping command name to command executor
        # self.commands: Dict[str, CommandExecutor] = None

        # mapping from a command name to the executor instance for it
        self.commands: Dict[str, CommandExecutor] = {}

        # internal caches of the first words of a command name, second words etc
        self._first_words = None
        self._second_words = None
        self._third_words = None

        self.update_commands(commands_def)

    def update_commands(self, commands_def: List[CommandDefinition]):
        """Update the commands in the internal registry
        
        Args:
            commands_def: the commands definition, loaded from file or elsewhere
        """
        # clear all these first
        self.commands = {}
        self._first_words = None
        self._second_words = None
        self._third_words = None

        for icommand, command_def in enumerate(commands_def):
            kwargs = command_def['kwargs']
            all_names = [command_def['name']] + command_def.get('aliases', [])
            for name in all_names:
                logger.debug('(%d) Loading command: %s', icommand, name)
                self.commands[name] = \
                    self.command_types[command_def['command_type']](self, **kwargs)

        self._set_cmd_name_words()

    @property
    def cmd_names(self) -> List[str]:
        """Returns a list of command names
        
        Returns:
            the command names
        """
        return list(self.commands.keys())

    def _set_cmd_name_words(self):
        """Set internal caches of command words
        """
        self._first_words = []
        self._second_words = []
        self._third_words = []
        for cmd_name in self.cmd_names:
            words = cmd_name.split()
            self._first_words.append(words[0])
            if len(words) > 1:
                self._second_words.append(words[1])
            if len(words) > 2:
                self._third_words.append(words[2])
            if len(words) > 3:
                raise NotImplementedError

    def cmd_name_words(self, indx: int = 0) -> List[str]:
        """Get the words in the first, second, etc position in all command
        names


        Args:
            indx: the position in the command name. 0 is the first word, one is
                the second word, etc (default: {0})
        
        Returns:
            list of words at given position in command name
        """
        if indx == 0:
            return self._first_words
        elif indx == 1:
            return self._second_words
        elif indx == 2:
            return self._third_words
        else:
            raise NotImplementedError

    def get_command_executor(self, cmd_name: str) -> CommandExecutor:
        """Get the executor instance for a given command name
        
        Args:
            cmd_name: the name of the command
        
        Returns:
            executor instance
        """
        return self.commands[cmd_name]


class CommandDispatcher:
    """Handles the execution of all single commands
    
    Parses and executes the text for any command. delegates the details of
    execution to subclasses of CommandExecutor.    
    """

    # all the different tokens that can be used for a multiplier post fix
    # note that the multiplier postfix is optional note.
    multiplier_postfixes = ['*', 'times', 'times', 'x', 'X']

    def __init__(self, cmd_reg: CommandRegistry):
        """Init
        
        Args:
            cmd_reg: the command
        """
        self.cmd_reg = cmd_reg

    def dispatch(self, command_text: str):
        """Dispatch a given raw command text for execution
                
        Args:
            command_text: the raw string command text, as output by the
                speech-to-text engine
        """
        
        logger.debug("Raw command: '{}'".format(command_text))

        cmd_name, cmd_mult, cmd_args = self.parse(command_text)
        
        executor = self.cmd_reg.get_command_executor(cmd_name)
        
        # execute cmd_mult times
        for _ in range(cmd_mult):
            executor.execute(stt_args=cmd_args)

    def convert_multiplier(self, token: str) -> Optional[int]:
        """Convert a command multiplier token into the actual number
                
        Args:
            token: the token from the raw command
        
        Returns:
            the converted multiplier, or None if it couldn't be converted
        """

        # hard-coded conversions from tokens to numbers. Accounts for edge
        # cases we've seen
        fixed_conversions = {
            'to': 2,
            'two': 2,
            'three': 3,
            'for': 4,
        }

        # first see if it's an integer
        try:
            cmd_multiplier = int(token)
        # if we don't find a number here, then see if it's in the fixed
        # conversions dictionary
        except ValueError:
            cmd_multiplier = fixed_conversions.get(token, None)
        return cmd_multiplier

    def parse(self, command_text: str) -> Tuple[str, int, List[str]]: #pylint: disable=too-many-branches
        """Parse a command text
        
        Rurns a raw command string into arguments for actual execution
        
        Args:
            command_text: the raw string command text, as output by the
                speech-to-text engine
        
        Returns:
            Tuple the command name, the execution multiplier, and arguments for
                the command
        """
        tokens = command_text.split(' ')

        # extracted command characteristics
        cmd_name_list = []
        cmd_multiplier = None
        cmd_args = None

        state = 'command_multiplier_0'
        itoken = 0
        while state != 'done' and itoken < len(tokens):
            token = tokens[itoken]
            # parse the actual number
            if state == 'command_multiplier_0':
                # if we find an integer, that's the command multiplier
                cmd_multiplier = self.convert_multiplier(token)
                if cmd_multiplier is not None:
                    state = 'command_multiplier_1'
                # if we don't find a number here, then it's implicit 1. Proceed
                # to command name
                else:
                    cmd_multiplier = 1
                    # go back a token because we're actually at the command name now
                    itoken -= 1
                    state = 'command_name_0'
            elif state == 'command_multiplier_1':
                # if there is a multiplier post fix token, we don't need to
                # do anything
                if token in self.multiplier_postfixes:
                    pass
                # the multiplier postfix is optional.
                else:
                    # go back a token because we're actually at the command name now
                    itoken -= 1
                state = 'command_name_0'
            # first word in the command name
            elif state == 'command_name_0':
                # see if the token is a known first word
                if token in self.cmd_reg.cmd_name_words(0):
                    cmd_name_list.append(token)
                    state = 'command_name_1'
                # there must be at least one expected word for it to be a real
                # command
                else:
                    raise Exception(f"Expected a known command name, found {token}")
            # second word in the command name (optional)
            elif state == 'command_name_1':
                # see if the token is a known second word
                if token in self.cmd_reg.cmd_name_words(1):
                    cmd_name_list.append(token)
                    state = 'command_name_2'
                # if there is no second word, we're in the command args now
                else:
                    state = 'args'
                    # go back a token because we're actually at the args
                    itoken -= 1
            # third word in the command name (optional)
            elif state == 'command_name_2':
                # see if the token is a known third word
                if token in self.cmd_reg.cmd_name_words(2):
                    cmd_name_list.append(token)
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
        cmd_name = ' '.join(cmd_name_list)
        assert cmd_name in self.cmd_reg.cmd_names
        
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