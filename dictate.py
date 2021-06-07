""" Main script for the dictation tool
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import platform
import queue
from threading import Thread

import click

plats_sys = platform.system()

if plats_sys == 'Linux':
    from ui.app_indicator_linux import app_indicator_thread, gtk_main_thread
if plats_sys == 'Darwin':
    from ui.app_indicator_mac import MenuBarManager
from ui.keyboard import keyb_listener
from ui.mouse import mouse_listener
from backend.manager import app_mngr
from backend.executor import executor_inst, do_executor
from backend.webspeech import do_webspeech
from ui.kb_controller import KBCntrlrWrapperManager

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

    # create the keyboard controller manager and start it
    kb_cntrl_mngr = KBCntrlrWrapperManager()
    kb_cntrl_mngr.start()
    
    if plats_sys == 'Darwin':
        # create the menu bar manager and start it
        menu_mngr = MenuBarManager()
        menu_mngr.start()

    executor_inst.setup(kb_cntrl_mngr)

    # set up threads
    webspeech_thread = Thread(target=do_webspeech, args=(raw_stt_output_q,
                                                         WEBSPEECH_HOST,
                                                         WEBSPEECH_PORT))
    executor_thread = Thread(target=do_executor, args=(raw_stt_output_q,))
    manager_thread = Thread(target=app_mngr.do_manager)
    
    # start the threads
    webspeech_thread.start()
    executor_thread.start()
    manager_thread.start()

    if plats_sys == 'Linux':
        app_indicator_thread.start()
        gtk_main_thread.start()

    # wait for them all to finish
    webspeech_thread.join()
    executor_thread.join()
    manager_thread.join()
    if plats_sys == 'Linux':
        app_indicator_thread.join()
        gtk_main_thread.join()

    kb_cntrl_mngr.terminate()
    if plats_sys == 'Darwin':
        menu_mngr.terminate()

if __name__ == '__main__':
    cli()
