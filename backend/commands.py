# pylint: disable=arguments-differ

from enum import Enum
import time
from typing import List, Dict, Any, Tuple, Optional

from pynput.keyboard import Controller, Key


class CommandExecutor:
    """Executes a command
    
    Virtual class, meant to be subclassed for specific command types    
    """

    def execute(self, stt_args: Optional[List[str]], **cmd_def_kwargs):
        """Execute the command, with given arguments
        
        should be overridden in subclasses

        Args:
            stt_args: list of string arguments received from speech to text
            cmd_def_kwargs: other keyword arguments from the command definition
        """
        raise NotImplementedError


class KeystrokeExec(CommandExecutor):
    """Executed a keystroke command, which is a series of 1 or more hotkeys
    
    Command name: 'keystroke'
    cmd_def_kwargs: 
        'keys': list of hotkeys to execute. Can also include "delay <float
            time>" to specify insertion of a delay
    
    Attributes:
        hotkey_separator: [description]
        modifiers_map: [description]
        }: [description]
        special_operand_keys: [description]
        }: [description]
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
        'tab': Key.tab
    }

    def __init__(self):
        self.keyboard_ctlr = Controller()

    def parse_hotkey(self, hotkey: str) -> Tuple[List[Enum], str]:
        """Parses a string specification for a hotkey into usable keys
        
        Given an input like 'ctrl-alt-a', returns a tuple of 
            (Key.ctrl, Key.alt, 'a'). Here, 'a' is the "operand" key.
        
        Args:
            hotkey: the hotkey string specifier
        
        Returns:
            a tuple of:
                - a list of modifiers Key.blah (the type of which is an Enum)
                - the string for the "operand" key.
        """
        hotkey_keys = hotkey.split(self.hotkey_separator)
        # modifiers should be at the front
        modifiers = hotkey_keys[:-1]
        operand_key = hotkey_keys[-1]
        modifiers_obj = [self.modifiers_map[mod] for mod in modifiers]
        assert operand_key not in self.modifiers_map
        # if there is a mapping in special operand keys, get it. otherwise
        # default to itself.
        operand_key = self.special_operand_keys.get(operand_key, operand_key)
        return modifiers_obj, operand_key

    def execute(self, stt_args: Optional[List[str]], keys: List[str]):
        """Execute command

        Note that when using system hotkeys like super+tab, you may need to
        insert a delay afterwards
        
        Args:
            stt_args: see superclass
            keys: list of sequential keystroke hotkeys, where each hotkey may be
                one regular key plus 0 or more modifiers. 
                Example: ['ctrl-c','alt-v']
        """
        # there should be no speech to text arguments for keystroke command
        assert stt_args is None
        for hotkey in keys:
            # deal with delay
            if hotkey.startswith('delay'):
                delay_time = float(hotkey.split()[1])
                time.sleep(delay_time)
                continue

            hotkey_keys = self.parse_hotkey(hotkey)
            # see https://pynput.readthedocs.io/en/latest/keyboard.html
            with self.keyboard_ctlr.pressed(*hotkey_keys[0]):
                self.keyboard_ctlr.press(hotkey_keys[1])
                self.keyboard_ctlr.release(hotkey_keys[1])

# class ChainCommandExec(CommandExecutor):
#     def __init__(self):
#         pass

#     def execute(self, commands: List[str]):
#         for command in commands:
#             pass
#             # execute command




CommandDefinition = Dict[str, Any]
CommandDefinitionKwargs = Dict[str, Any]

class CommandRegistry:
    """Maintains a registry of all the known commands
    """
    # the mapping
    command_types = {
        'keystroke': KeystrokeExec(), 
        'delete': KeystrokeExec(), 
        'command_chain': ChainCommandExec()
    }

    def __init__(self, commands_def: List[CommandDefinition]):
        """Init
        
        Args:
            commands_def: the commands definition, loaded from file or elsewhere
        """

        # mapping from a command name to the executor instance for it
        self._reg_exec: Dict[str, CommandExecutor] = {}
        # mapping from a command name to the keyword arguments for it specified
        # in the command definition
        # example: 'dash' -> {"keys": ["-"]}
        self._reg_cmd_def_kwargs: Dict[str, CommandDefinitionKwargs] = {}

        for command_def in commands_def:
            self._reg_exec[command_def['name']] = \
                self.command_types[command_def['command']]
            self._reg_cmd_def_kwargs[command_def['name']] = \
                command_def['kwargs']

        self._cmd_names = None
        # internal caches of the first words of a command name, second words etc
        self._first_words = None
        self._second_words = None
        self._third_words = None
        self._set_cmd_name_words()

    @property
    def cmd_names(self) -> List[str]:
        """Returns a list of command names
        
        Returns:
            the command names
        """
        if not self._cmd_names:
            self._cmd_names = list(self._reg_exec.keys())
        return self._cmd_names

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
        return self._reg_exec[cmd_name]
    
    def get_command_def_kwargs(self, cmd_name: str) -> CommandDefinitionKwargs:
        """Get the keyword args from the command definition for a given command
        
        Args:
            cmd_name: the name of the command
        
        Returns:
            the keyword args
        """
        return self._reg_cmd_def_kwargs[cmd_name]



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
        
        cmd_name, cmd_mult, cmd_args = self.parse(command_text)
        
        executor = self.cmd_reg.get_command_executor(cmd_name)
        
        # execute cmd_mult times
        for icmd in range(cmd_mult):
            cmd_def_kwargs = self.cmd_reg.get_command_def_kwargs(cmd_name)
            executor.execute(stt_args=cmd_args, **cmd_def_kwargs)

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
                try:
                    cmd_multiplier = int(token)
                    state = 'command_multiplier_1'
                # if we don't find a number here, then it's implicit 1. Proceed
                # to command name
                except ValueError:
                    cmd_multiplier = 1
                    state = 'command_name_0'
            elif state == 'command_multiplier_1':
                # if there is a multiplier post fix token, we don't need to
                # do anything
                if token in self.multiplier_postfixes:
                    pass
                # the multiplier postfix is optional. in that case, we're at the
                # start of the command name.
                else:
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
                # if there is no second word, we're in the command args
                else:
                    state = 'args'
                    itoken -= 1
            # third word in the command name (optional)
            elif state == 'command_name_1':
                # see if the token is a known third word
                if token in self.cmd_reg.cmd_name_words(2):
                    cmd_name_list.append(token)
                    state = 'args'
                # if there is no third word, we're in the command args
                else:
                    state = 'args'
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

if __name__ == "__main__":

    import json
    with open('example_commands.json', 'r') as f:
        commands_def_in = json.load(f)
    cmd_reg = CommandRegistry(commands_def_in)

    cmd_exec = CommandDispatcher(cmd_reg)
    # import ipdb
    # ipdb.set_trace()
    # cmd_exec.dispatch('12 times dash')
    cmd_exec.dispatch('3 dog')



# from python_utils.file_utils import unjson_thing

# raw = 'yo how are you doing <escape> 3 tabitha, left click'

# island_commands = ['delete']

# def parse_utterance(utterance: str):
#     words = raw.split()
#     first_word = words[0]
#     if first_word in island_commands:
#         execute_command(words)
#     # not an island, there's mixed stt and (potentially) commands
#     else:
#         commands_words = []
#         command_words = []
#         # words to print as literals ("speech to [final output] text" words)
#         stt_words_to_print = []
#         in_command = False
#         # did we see ESCAPE_WORD on the last iteration?
#         last_iter_was_escape = False
#         for word in words:
#             # we are either building up stt words or command words
#             if word != ESCAPE_WORD:
#                 if in_command:
#                     command_words.append(word)
#                 else:
#                     stt_words_to_print.append(word)
#             else:
#                 # end of command, need to execute it
#                 if in_command:
#                     execute_command(command_words)
#                 # we're starting a command, so need to print out the stt words
#                 else:
#                     print_to_output(stt_words_to_print)
#                     stt_words_to_print = []
#                 in_command = not in_command

#             # reset this state
#             if last_iter_was_escape:
#                 last_iter_was_escape = False

