
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

from typing import List, Dict, Any, Tuple

from pynput.keyboard import Controller


class Command:
    pass
    # def execute(self, args: List[str]):


class KeystrokeCommand(Command):
    modifiers = ['ctrl', 'alt', 'super', 'shift']

    def __init__(self):
        pass

    def execute(self, keys: List[str]):
        """Execute command
        
        Args:
            keys: list of sequential keystroke hotkeys, where each hotkey may be
                one regular key plus 0 or more modifiers
        """
        for hotkey in keys:
            #todo
            pass
            # keyboard_ctlr.type(the_text)

class ChainCommand(Command):
    def __init__(self):
        pass

    def execute(self, commands: List[str]):
        for command in commands:
            pass
            # execute command




CommandDefinition = Dict[str, Any]

class CommandRegistry:
    """Maintains a registry of all the known commands
    """
    # the mapping
    command_types = {
        'keystroke': KeystrokeCommand(), 
        'delete': KeystrokeCommand(), 
        'command_chain': ChainCommand()
    }

    def __init__(self, commands_def: List[CommandDefinition]):
        self._reg = {}

        for command_def in commands_def:
            self._reg[command_def['name']] = \
                self.command_types[command_def['command']]

        self._cmd_names = None
        self._first_words = None
        self._second_words = None
        self._third_words = None
        self._set_cmd_name_words()

    @property
    def cmd_names(self) -> List[str]:
        if not self._cmd_names:
            self._cmd_names = list(self._reg.keys())
        return self._cmd_names

    def _set_cmd_name_words(self):
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
        if indx == 0:
            return self._first_words
        elif indx == 1:
            return self._second_words
        elif indx == 2:
            return self._third_words
        else:
            raise NotImplementedError




import json
with open('example_commands.json', 'r') as f:
    commands_def = json.load(f)
cmd_reg = CommandRegistry(commands_def)

class CommandExecutive:

    # all the different tokens that can be used for a multiplier post fix
    # note that the multiplier postfix is optional note.
    multiplier_postfixes = ['*', 'times', 'times', 'x', 'X']

    def execute(self, command_text: str):
        
        # cmd_name, cmd_mult, cmd_args = self.parse(command_text)
        print(self.parse(command_text))

    def parse(self, command_text: str) -> Tuple[str, int, List[str]]:
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
                cmd_multiplier = int(token)
                state = 'command_multiplier_1'
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
                if token in cmd_reg.cmd_name_words(0):
                    cmd_name_list.append(token)
                    state = 'command_name_1'
                # there must be at least one expected word for it to be a real
                # command
                else:
                    raise Exception(f"Expected a known command name, found {token}")
            # second word in the command name (optional)
            elif state == 'command_name_1':
                # see if the token is a known second word
                if token in cmd_reg.cmd_name_words(1):
                    cmd_name_list.append(token)
                    state = 'command_name_2'
                # if there is no second word, we're in the command args
                else:
                    state = 'args'
                    itoken -= 1
            # third word in the command name (optional)
            elif state == 'command_name_1':
                # see if the token is a known third word
                if token in cmd_reg.cmd_name_words(2):
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
        assert cmd_name in cmd_reg.cmd_names
        
        return cmd_name, cmd_multiplier, cmd_args


class CompoundCommandExecutive:
    def __init__(self):
        self.command_exe = CommandExecutive()

    def execute(self, text: str):
        command_texts = text.split(',')
        # execute each command in order
        for text in command_texts:
            self.command_exe.execute(text)

if __name__ == "__main__":

    cmd_exec = CommandExecutive()
    import ipdb
    ipdb.set_trace()
    cmd_exec.execute('12 times dash')
    cmd_exec.execute('3 dash yo dawg')