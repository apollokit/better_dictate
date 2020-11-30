""" Main script for the dictation tool
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import queue

import click 

# from audio import audio_thread, read_audio_from_file
from ui.app_indicator import app_indicator_thread, gtk_main_thread
from ui.keyboard import keyb_listener
from ui.mouse import mouse_listener
from backend.webspeech import webspeech_thread
from backend.parser import parser_thread

WEBSPEECH_HOST='localhost'
WEBSPEECH_PORT=5678

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
    # speech to (raw) text output
    raw_stt_output_q = queue.Queue()

    # start the keyboard and mouse listeners
    # note these are also threads
    keyb_listener.start()
    mouse_listener.start()

    # note that shutdown/quit event can be invoked from app_indicator.py
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        futures.append(executor.submit(
            webspeech_thread, 
            raw_stt_output_q,
            WEBSPEECH_HOST,
            WEBSPEECH_PORT))
        futures.append(executor.submit(
            parser_thread,
            raw_stt_output_q))
        futures.append(executor.submit(
            app_indicator_thread))
        futures.append(executor.submit(
            gtk_main_thread))
        for future in as_completed(futures):
            logger.debug(f"Thread exit: {repr(future.exception())}")

if __name__ == '__main__':
    cli()