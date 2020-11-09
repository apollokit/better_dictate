
from python_utils.file_utils import unjson_thing

raw = 'yo how are you doing <escape> 3 tabitha, left click'

island_commands = ['delete']

def parse_utterance(utterance: str):
    words = raw.split()
    first_word = words[0]
    if first_word in island_commands:
        execute_command(words)
    # not an island, there's mixed stt and (potentially) commands
    else:
        commands_words = []
        command_words = []
        # words to print as literals ("speech to [final output] text" words)
        stt_words_to_print = []
        in_command = False
        # did we see ESCAPE_WORD on the last iteration?
        last_iter_was_escape = False
        for word in words:
            # we are either building up stt words or command words
            if word != ESCAPE_WORD:
                if in_command:
                    command_words.append(word)
                else:
                    stt_words_to_print.append(word)
            else:
                # end of command, need to execute it
                if in_command:
                    execute_command(command_words)
                # we're starting a command, so need to print out the stt words
                else:
                    print_to_output(stt_words_to_print)
                    stt_words_to_print = []
                in_command = not in_command

            # reset this state
            if last_iter_was_escape:
                last_iter_was_escape = False
