
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

from typing import List, Dict

from pynput.keyboard import Controller


class Command:
    pass
    def execute(args: List[str]):


class KeystrokeCommand(Command):
    modifiers = ['ctrl', 'alt', 'super', 'shift']

    def __init__(self):
        pass

    def execute(keys: List[str]):
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

    def execute(commands: List[str]):
        for command in commands:
            pass
            # execute command


class CommandExecutive:
    def execute(text: str):


class CompoundCommandExecutive:
    def __init__(self):
        self.command_exe = CommandExecutive()

    def execute(text: str):
        command_texts = text.split(',')
        # execute each command in order
        for text in command_texts:
            self.command_exe.execute(text)


CommandDefinition = Dict[str, Any]

class CommandRegistry:
    # mapping from command name in the commands definition file to an
    # instance of the class
    command_types = {
        'keystroke': KeystrokeCommand(), 
        'command_chain': ChainCommand()
    }

    def __init__(self, commands_def: List[CommandDefinition]):
        self.reg = {}

        for command_def in commands_def:
            self.reg[command_def['name']] = \
                self.command_types[command_def['command']]

if __name__ 