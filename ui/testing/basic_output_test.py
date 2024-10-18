from pynput.keyboard import Controller
import time

# Create an instance of the Controller
keyboard = Controller()

# Function to type "hello world"
def type_hello_world():
    # Wait for 1 second before typing (optional)
    time.sleep(1)
    
    print('typing')
    # Type "hello world"
    keyboard.type("hello world")

# Call the function to type "hello world"
type_hello_world()
