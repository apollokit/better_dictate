"""Functionality for dealing with mouse interactions

lifted from: https://pynput.readthedocs.io/en/latest/mouse.html#
"""

import time
from pynput import mouse

from backend.manager import event_mngr

# The amount of time less than which a second click is considered a double
# click
DOUBLECLICK_DELTA_S = 0.3
# amount of time after which a new click clears the double-click state
DOUBLECLICK_CLEAR_S = 2.0

# def on_move(x, y):
#     mouse_moved_event.set()

class MouseManager:
    def __init__(self):
        self.last_click_time = time.time()

    def on_click(self, x, y, button, pressed):
        """Handle mouse clicks
        
        when the mouse is released, mouse_clicked it is always set

        double-clicking works like this:
        - When the mouse is double clicked (with the second click coming
        within DOUBLECLICK_DELTA_S), the event is set
        - the event is only cleared when a fresh click comes after DOUBLECLICK_CLEAR_S
        
        the intent for double-clicking is to allow a double click to set some
        useful state. The "clear" guard is so that we can triple click and not
        clear that state (because when you double-click a word in linux
        usually that selects it - A triple click will both trigger the
        double click and clear the selection)
        """

        # if we're releasing the mouse
        if not pressed:
            curr_time = time.time()
            event_mngr.mouse_clicked.set()

            if curr_time - self.last_click_time <= DOUBLECLICK_DELTA_S:
                event_mngr.mouse_doubleclicked.set()
            if curr_time - self.last_click_time > DOUBLECLICK_CLEAR_S:
                event_mngr.mouse_doubleclicked.clear()
            self.last_click_time = curr_time

# def on_scroll(x, y, dx, dy):
#     print('Scrolled {0} at {1}'.format(
#         'down' if dy < 0 else 'up',
#         (x, y)))

mouse_manager = MouseManager()
# note that this is a thread
mouse_listener = mouse.Listener(
    on_move=None,
    on_click=mouse_manager.on_click,
    on_scroll=None)
