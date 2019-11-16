import threading

# event used to signal shutdown across threads
# once set, this should NEVER BE CLEARED!
shutdown_event = threading.Event()