"""Functionality for dealing with mouse interactions

lifted from: https://pynput.readthedocs.io/en/latest/mouse.html#
"""

from pynput import mouse

from backend.manager import event_mngr

# def on_move(x, y):
#     mouse_moved_event.set()

def on_click(x, y, button, pressed):
    event_mngr.mouse_clicked.set()

# def on_scroll(x, y, dx, dy):
#     print('Scrolled {0} at {1}'.format(
#         'down' if dy < 0 else 'up',
#         (x, y)))

# note that this is a thread
mouse_listener = mouse.Listener(
    on_move=None,
    on_click=on_click,
    on_scroll=None)
