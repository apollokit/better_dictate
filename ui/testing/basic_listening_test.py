from pynput import keyboard

def on_press(key):
    print(f'Key {key} pressed')

def on_release(key):
    print(f'Key {key} released')
    if key == keyboard.Key.esc:
        return False  # Stop listener

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()