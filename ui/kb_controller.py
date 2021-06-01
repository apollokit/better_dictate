
from collections import namedtuple
import logging
import multiprocessing
# multiprocessing.set_start_method('forkserver')
from multiprocessing import Process, Queue
import time

from pynput.keyboard import Controller


form = "%(asctime)s %(levelname)-8s %(name)-15s %(message)s"
logging.basicConfig(format=form,
                    datefmt="%H:%M:%S")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

KBCntrlCommand = namedtuple('KBCntrlCommand', 'name, payload')

def pynp_kb_cntrl_job(command_queue: Queue):
    kb_cntrl = Controller()
    logger.info('Pynput keyboard controller job started')

    while True:
        command: KBCntrlCommand = command_queue.get()
        # tap key
        if command.name == 'tap':
            kb_cntrl.tap(command.payload)
        # kill the loop
        elif command.name == 'kill':
            break
        else:
            raise NotImplementedError(f'No command "{command.name}"')

class KBCntrlWrapper:
    pass
#     _command_queue = Queue()
#     _kbc_proc = None

#     def __init__(self):
#         KBCntrlWrapper._kbc_proc = Process(target=pynp_kb_cntrl_job, args=(KBCntrlWrapper._command_queue, ))
#         KBCntrlWrapper._kbc_proc.start()

#         self._kbc_proc = KBCntrlWrapper._kbc_proc
#         self._command_queue = KBCntrlWrapper._command_queue

#     def kill(self):
#         # todo make sure queue is clear, per https://docs.python.org/3/library/multiprocessing.html#programming-guidelines
#         # todo throw error if already joined
#         self._kbc_proc.join()

#     def tap(self, char: str):
#         self._command_queue.put(char)

class KBCntrlWrapperManager:
    """Manages the keyboard controller. Only one instance of this class should be
    created, and used everywhere needed

    This class is needed as a container for the separate process spun up for 
    managing the pynput keyboard controller. That separate process is needed 
    because threading doesn't work with pynput on Mac.

    Notes: an instance of this class can only be created *in a main module*. 
    Cannot be created as a module-level variable. Multiprocessing doesn't like that,
    at least in python3.8, and will complain about: 
        "RuntimeError: 
            An attempt has been made to start a new process before the
            current process has finished its bootstrapping phase.
        "
    """

    def __init__(self):
        self._command_queue = Queue()
        self._kbc_proc = Process(target=pynp_kb_cntrl_job, 
            args=(self._command_queue, ))
        self._kbc_proc.start()

    def get_kb_cntrl_wrapper(self) -> KBCntrlWrapper:
        pass

    def kill(self):
        self._command_queue.put(KBCntrlCommand('kill', None))
        self._kbc_proc.join()


# singleton module-level keyboard controller. Only want one because it spawns
# a new process under the hood
# keyboard_controller = None

# def get_keyboard_controller():
#     # return if already created
#     if keyboard_controller:
#         return keyboard_controller
#     # make it
#     keyboard_controller = KBCntrlWrapper()
#     return keyboard_controller

if __name__ == '__main__':
    # this_keyboard_controller = KBCntrlWrapper()
    # this_keyboard_controller.tap('l')

    # _command_queue = Queue()
    # yo = Process(target=pynp_kb_cntrl_job, args=(_command_queue, ))
    # # yo = Process(target=pynp_kb_cntrl_job, args=(12, ))
    # yo.start()
    # _command_queue.put('l')
    # _command_queue.put('b')
    # _command_queue.put('c')
    # yo.join()

    # kb_cntrl = Controller()
    # kb_cntrl.tap('l')

    mngr = KBCntrlWrapperManager()
    mngr._command_queue.put(KBCntrlCommand('tap', 'l'))
    mngr._command_queue.put(KBCntrlCommand('tap', 'b'))
    mngr._command_queue.put(KBCntrlCommand('tap', 'l'))
    mngr.kill()
