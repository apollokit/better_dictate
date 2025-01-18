""" Main script for the dictation tool
"""

import logging
import platform
import queue
from threading import Thread
import signal

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
WEBSPEECH_PORT=5682

form = "%(asctime)s %(levelname)-8s %(name)-15s %(message)s"
logging.basicConfig(format=form,
                    datefmt="%H:%M:%S")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class BetterDictateApp:
    def start(self):
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
        self.kb_cntrl_mngr = KBCntrlrWrapperManager()
        self.kb_cntrl_mngr.start()
        
        if plats_sys == 'Darwin':
            # create the menu bar manager and start it
            self.menu_mngr = MenuBarManager()
            self.menu_mngr.start()

        executor_inst.setup(self.kb_cntrl_mngr)

        # set up threads
        self.webspeech_thread = Thread(target=do_webspeech, args=(raw_stt_output_q,
                                                             WEBSPEECH_HOST,
                                                             WEBSPEECH_PORT))
        self.executor_thread = Thread(target=do_executor, args=(raw_stt_output_q,))
        self.manager_thread = Thread(target=app_mngr.do_manager)
        
        # start the threads
        self.webspeech_thread.start()
        self.executor_thread.start()
        self.manager_thread.start()

        if plats_sys == 'Linux':
            app_indicator_thread.start()
            gtk_main_thread.start()

    def stop(self):
        app_mngr.signal_quit()

    def wait_and_close(self):
        # wait for them all to finish
        self.webspeech_thread.join()
        self.executor_thread.join()
        self.manager_thread.join()
        if plats_sys == 'Linux':
            app_indicator_thread.join()
            gtk_main_thread.join()

        self.kb_cntrl_mngr.terminate()
        if plats_sys == 'Darwin':
            self.menu_mngr.terminate()
        logger.info('Have a nice day!')

the_app = BetterDictateApp()

# if ctrl+c is pressed, gracefully bring down the app
# note: wait_and_close() executes twice when you ctrl+c to kill, but 
#  not a big deal
def interrupt_handler(sig, frame):
    the_app.stop()
    the_app.wait_and_close()
signal.signal(signal.SIGINT, interrupt_handler)

if __name__ == '__main__':
    the_app.start()
    the_app.wait_and_close()