# pip install PyQt5

from multiprocessing import Process, Queue

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction


def do_proc(command_queue):
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    # Create the icon
    icon = QIcon("../bad_pun_boy.png")

    # Create the tray
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)

    # Create the menu
    menu = QMenu()
    action = QAction("A menu item")
    menu.addAction(action)

    # Add a Quit option to the menu.
    quit = QAction("Quit")
    quit.triggered.connect(app.quit)
    menu.addAction(quit)

    # Add the menu to the tray
    tray.setContextMenu(menu)

    app.exec_()

if __name__ == "__main__":
    command_queue = Queue()
    proc = Process(target=do_proc,
                             args=(command_queue, ))

    proc.start()
    proc.join()