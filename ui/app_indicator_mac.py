# see:
# https://www.pythongasm.com/menubar-app-for-macos-using-python/
# https://rumps.readthedocs.io/en/latest/index.html

import logging
from multiprocessing import Process, Queue
from os import path
import time
from threading import Thread

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction

from backend.manager import app_mngr

form = "%(asctime)s %(levelname)-8s %(name)-15s %(message)s"
logging.basicConfig(format=form,
                    datefmt="%H:%M:%S")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

abs_file_dir = path.dirname(path.abspath(__file__))

# Icon paths
# this has to be absolute...
# use bad pun boy for the time being :bad_pun:
active_icon_path = path.join(abs_file_dir, '..', 'ui', 'listening.png')
sleeping_icon_path = path.join(abs_file_dir, '..', 'ui', 'sleeping2.png')

class UpdaterThread(QThread):
    def __init__(self, 
            command_queue: Queue, 
            app: QApplication, 
            tray: QSystemTrayIcon, 
            active_icon: QIcon, 
            sleeping_icon: QIcon):
        super().__init__()
        self._tray = tray
        self._active_icon = active_icon
        self._sleeping_icon = sleeping_icon
        self._app = app
        # self._tray.setIcon(active_icon)

        self._command_queue = command_queue

    def run(self):
        while True:
            # blocks until something available
            command = self._command_queue.get()
            if command == 'active':
                self._tray.setIcon(self._active_icon)
            elif command == 'sleep':
                self._tray.setIcon(self._sleeping_icon)
            elif command == 'quit':
                self._app.quit()
            else: 
                raise NotImplementedError
            

def menu_bar_job(menu_command_to_queue: Queue):
    logger.info('Menu bar job started')

    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    # Create the icon
    active_icon = QIcon(active_icon_path)
    sleeping_icon = QIcon(sleeping_icon_path)

    # Create the tray
    tray = QSystemTrayIcon()
    tray.setIcon(active_icon)
    tray.setVisible(True)

    # Create the menu
    menu = QMenu()

    # Add a Quit option to the menu.
    quit = QAction("Quit")
    quit.triggered.connect(app.quit)
    menu.addAction(quit)

    # Add the menu to the tray
    tray.setContextMenu(menu)

    updater_thread = UpdaterThread(menu_command_to_queue, 
        app, tray, active_icon, sleeping_icon)
    updater_thread.start()

    app.exec_()

class MenuBarManager:
    def __init__(self):
        # queue to send commands to the menu bar proc
        self._menu_command_to_queue = Queue()

        self._menu_bar_proc = Process(target=menu_bar_job, 
            args=(self._menu_command_to_queue,))
        self._manager_thread = Thread(target=self.do_manage)

        self._last_app_mngr_state_sleep = True

    def start(self):
        """Start the process. Need to call terminate() at some point too 
        """
        self._menu_bar_proc.start()

        self._manager_thread.start()

    def terminate(self):
        """Terminate KB controller process

        Should be called when the separate keyboard controller process needs to be spun down
        """
        # end the proc
        # todo make sure queue is clear, per https://docs.python.org/3/library/multiprocessing.html#programming-guidelines
        # todo throw error if already joined
        self._menu_bar_proc.join()
        self._manager_thread.join()
        logger.info('MenuBarManager process and thread terminated')

    def do_manage(self):
        while True:
            # protect against quitting condition before doing anything with the
            # app _indicator. This is to avoid any race conditions with gtk
            # shutting down
            if app_mngr.quitting:
                # break the loop if we're quitting
                self._menu_command_to_queue.put('quit')
                break

            # set the app icon depending on whether we're sleeping or not
            if app_mngr.sleeping:
                if not self._last_app_mngr_state_sleep:
                    self._menu_command_to_queue.put('sleep')
            else:
                if self._last_app_mngr_state_sleep:
                    self._menu_command_to_queue.put('active')
            
            self._last_app_mngr_state_sleep = app_mngr.sleeping

            # the user has selected to quite from the UI, so kill the overall app
            if not self._menu_bar_proc.is_alive():
                app_mngr.signal_quit()

            time.sleep(0.01)

