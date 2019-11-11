# usage: after start, press key 'a' to start the processing thread counting.
# Press 'a' again to stop it. Continue till you get bored.

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from pynput import keyboard

# event that signals start/stop for processor
ctrl_signal = threading.Event()

def processor():
    i = 0
    print("Starting processor")
    while True:
        if ctrl_signal.is_set():
            print(f'foo {i}')
            i += 1
        time.sleep(1)
    print("Stopping processor")

def on_press(key):
    pass
    # print('Key {} pressed.'.format(key))

def on_release(key):
    # print('Key {} released.'.format(key))
    if str(key) == "'a'":
        # print('a pressed...')
        if not ctrl_signal.is_set():
            print('setting ctrl_signal')
            ctrl_signal.set()
        else:
            print('releasing ctrl_signal')
            ctrl_signal.clear()
    if str(key) == 'Key.esc':
        print('Exiting...')
        return False

listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.start()

with ThreadPoolExecutor(max_workers=1) as executor:
    futures = []
    futures.append(executor.submit(processor))
    for future in as_completed(futures):
        print(repr(future.exception()))

