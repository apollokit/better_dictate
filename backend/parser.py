""" Thread and utilities for audio input.
"""

import json
import logging
from os import path
import threading
from queue import Queue, Empty
import sys
import traceback
from typing import Dict

from pynput.keyboard import Controller

from backend.commands import CommandDispatcher, CommandRegistry
from backend.manager import app_mngr, event_mngr
from backend.text import TextWriter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DictateParser:
    ESCAPE_WORD = 'dog'
    ISLAND_COMMAND_WORD = 'do'

    # hard-code the commands file for now
    commands_file = path.join(path.dirname(__file__), 'commands.json')

    def __init__(self):
        ## create the command dispatcher

        with open(self.commands_file, 'r') as f:
            commands_def = json.load(f)
        self.cmd_reg = CommandRegistry(commands_def)
        self.cmd_exec = CommandDispatcher(self.cmd_reg)
        # lock to prevent updating the command registry in the middle of parsing
        self._cmd_reg_lock = threading.Lock()

        ## create the text writer
        self.text_writer = TextWriter()


    def reload_commands(self):
        """Reload/update the commands in the command registry
        """
        logger.info('Loading commands from file: %s', self.commands_file)
        try:
            with open(self.commands_file, 'r') as f:
                commands_def = json.load(f)
            self._cmd_reg_lock.acquire()
            self.cmd_reg.update_commands(commands_def)
        except json.decoder.JSONDecodeError:
            logger.error('Error loading %s', self.commands_file)
        finally:
            self._cmd_reg_lock.release()

    def parse_and_execute(self, raw_utterance: str):
        """Parse and take action upon the raw text output from an utterance
        
        Args:
            raw_utterance: the text directly out of the speech-to-text engine
        """
        text = raw_utterance
        text = text.lower()
        text = text.strip()

        words = text.split()
        first_word = words[0]
        
        self._cmd_reg_lock.acquire()

        try:
            # if the utterance starts with the ISLAND_COMMAND_WORD, it's an
            # "island", or stand-alone command. Dispatch that for execution
            # immediately
            if first_word == self.ISLAND_COMMAND_WORD:
                logger.info("DictateParser: island command")
                self.cmd_exec.dispatch(' '.join(words[1:]))

            # not an island, there's mixed stt and (potentially) commands
            else:
                idispatch = 0
                command_words = []
                # text that we'll format and print out as straight speech to text
                raw_text_words = []
                in_command = False
                # did we see ESCAPE_WORD on the last iteration?
                # last_iter_was_escape = False
                for word in words:
                    # we are either building up raw text or command words
                    if word != self.ESCAPE_WORD:
                        if in_command:
                            command_words.append(word)
                        else:
                            raw_text_words.append(word)
                    else:
                        # end of command, need to execute it
                        if in_command:
                            logger.info("DictateParser: dispatch command ({})".format(idispatch))
                            self.cmd_exec.dispatch(' '.join(command_words))
                            command_words = []
                            idispatch += 1
                        # we're starting a command, so need to print out the raw text
                        else:
                            logger.info("DictateParser: dispatch text ({})".format(idispatch))
                            self.text_writer.dispatch(' '.join(raw_text_words))
                            raw_text_words = []
                            idispatch += 1
                        in_command = not in_command

                # handle the end
                if in_command:
                    logger.info("DictateParser: dispatch command ({})".format(idispatch))
                    self.cmd_exec.dispatch(' '.join(command_words))
                else:
                    logger.info("DictateParser: dispatch text ({})".format(idispatch))
                    self.text_writer.dispatch(' '.join(raw_text_words))


        # No except here, so any exceptions pass up the stack 

        finally:
            self._cmd_reg_lock.release()
        

parser_inst = DictateParser()

def parser_thread(raw_stt_output_q: Queue):
    """ Execution thread for parsing and acting output from inference
    
    Args:
        raw_stt_output_q: contains output string text from the text to speech
            engine.
    """

    logger.info("Parser thread ready")
    # the main thread loop. Go forever.
    while True:
        try:
            # get raw text from the queue
            raw_utterance: str = raw_stt_output_q.get(
                block=True, timeout=0.1)

            logger.debug("Got: '{}'".format(raw_utterance))
            
            try:
                parser_inst.parse_and_execute(raw_utterance)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_traceback)
                # logger.info("Parsing error: {}".format(str(e)))
            
        # queue was empty up to timeout
        except Empty:
            # check if it's time to close shop
            if app_mngr.quitting: 
                break
            
# if __name__ == "__main__":
#     import time

#     form = "%(asctime)s %(levelname)-8s %(name)-15s %(message)s"
#     logging.basicConfig(format=form,
#                         datefmt="%H:%M:%S")

#     parser_inst.saw_user_action = False
#     raw_utterance = "hey there i've got dog test"
#     time.sleep(2)
#     parser_inst.parse_and_execute(raw_utterance)