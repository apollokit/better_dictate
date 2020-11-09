""" Main script for the dictation tool
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import logging
import time
import threading
import queue

import click 
import numpy as np
from nptyping import Array
from pynput import keyboard
import wave

# from audio import audio_thread, read_audio_from_file
from backend.dictate_globals import events
from backend.keyboard import keyb_listener
from backend.webspeech import webspeech_thread
from backend.parser import DictateParser

form = "%(asctime)s %(levelname)-8s %(name)-15s %(message)s"
logging.basicConfig(format=form,
                    datefmt="%H:%M:%S")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@click.group()
def cli():
    pass

@cli.command()
@click.option("--audio_file", type=str, default=None,
    help="Path to an audio file. If provided, inference will be run on it and"
    "then the script will exit.")
@click.option("--inference_output_file", type=str,
    default="inference_output.json",
    help="Path of json file in which to store benchmark output from"
        "inference")
def go(
    audio_file: str,
    inference_output_file: str
    ):
    logging.info('Starting up')

    # interactive stuff

    # data structures for inter-thread communication
    # queue for captured audio frames
    audio_frames_q = queue.Queue()
    # speech to (raw) text output
    raw_stt_output_q = queue.Queue()

    keyb_listener.start()

    parser = DictateParser()

    # note that shutdown event can be invoked from keyboard.py
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        futures.append(executor.submit(
            webspeech_thread, 
            raw_stt_output_q,
            events))
        futures.append(executor.submit(
            parser.parser_thread,
            raw_stt_output_q,
            events))
        # if not shutdown_event.is_set():
        for future in as_completed(futures):
            logger.debug(f"Thread exit: {repr(future.exception())}")

if __name__ == '__main__':
    cli()