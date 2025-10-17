# see:
# https://www.pythongasm.com/menubar-app-for-macos-using-python/
# https://rumps.readthedocs.io/en/latest/index.html

import logging
from multiprocessing import Process, Queue
from os import path
import time
from threading import Thread
from queue import Empty as QueueEmpty  # for non-blocking reads

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
            
# event names
EV_TOGGLE_SLEEP = "toggle_sleep"
EV_UI_QUIT = "ui_quit"

# --- menu process ---

def menu_bar_job(menu_command_to_queue: Queue, menu_event_from_ui: Queue):
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


    # Add a sleep/wake option to the menu.
    switch_state = QAction("Sleep/Wake")
    # On click, emit an event. Your manager decides what to do.
    switch_state.triggered.connect(lambda _checked=False: menu_event_from_ui.put(EV_TOGGLE_SLEEP))
    menu.addAction(switch_state)

    # add an empty action just to avoid accidentally hitting quit too much
    empty_action = QAction("-")
    menu.addAction(empty_action)

    # Add a Quit option to the menu.
    quit_action = QAction("Quit")
    # Instead of closing the app directly, emit an event up to the manager.
    quit_action.triggered.connect(lambda: menu_event_from_ui.put(EV_UI_QUIT))
    menu.addAction(quit_action)

    # Add the menu to the tray
    tray.setContextMenu(menu)

    updater_thread = UpdaterThread(menu_command_to_queue, app, tray, active_icon, sleeping_icon)
    updater_thread.start()

    app.exec_()

# --- manager side ---

class MenuBarManager:
    def __init__(self):
        # queue manager -> menu (icon updates, quit)
        self._menu_command_to_queue = Queue()

        # queue menu -> manager (user clicks)
        self._menu_event_from_ui = Queue()

        self._menu_bar_proc = Process(
            target=menu_bar_job,
            args=(self._menu_command_to_queue, self._menu_event_from_ui),
        )
        self._manager_thread = Thread(target=self.do_manage, daemon=True)

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
        self._menu_command_to_queue.put('quit')
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

            # Handle UI -> manager events without blocking
            try:
                while True:
                    ev = self._menu_event_from_ui.get_nowait()
                    if ev == EV_TOGGLE_SLEEP:
                        app_mngr.toggle_sleep()
                    elif ev == EV_UI_QUIT:
                        app_mngr.signal_quit()
                        self._menu_command_to_queue.put('quit')
                        return
                    else:
                        logger.warning(f"Unknown menu event: {ev}")
            except QueueEmpty:
                pass

            # Reflect current app state in tray icon
            if app_mngr.sleeping:
                if not self._last_app_mngr_state_sleep:
                    self._menu_command_to_queue.put('sleep')
            else:
                if self._last_app_mngr_state_sleep:
                    self._menu_command_to_queue.put('active')
            self._last_app_mngr_state_sleep = app_mngr.sleeping

            # Fallback: if tray proc died unexpectedly, shut down app
            if not self._menu_bar_proc.is_alive():
                app_mngr.signal_quit()
                break

            time.sleep(0.01)
