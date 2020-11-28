"""Functionality for dealing with mouse interactions

lifted from: https://pynput.readthedocs.io/en/latest/mouse.html#
"""

from pynput import mouse

from backend.dictate_globals import events

mouse_moved_event = events['mouse_moved_parser']
mouse_clicked_event = events['mouse_clicked_parser']

def on_move(x, y):
    mouse_moved_event.set()

def on_click(x, y, button, pressed):
    mouse_clicked_event.set()

# def on_scroll(x, y, dx, dy):
#     print('Scrolled {0} at {1}'.format(
#         'down' if dy < 0 else 'up',
#         (x, y)))

# note that this is a thread
mouse_listener = mouse.Listener(
    on_move=on_move,
    on_click=on_click,
    on_scroll=None)
