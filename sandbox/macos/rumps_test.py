# pip install rumps

import rumps

@rumps.clicked("Weird Menu Item")
@rumps.clicked("Saner Menu Item")
def hello(sender):
    print(f"Hello from {sender.title}")

print("hey")

app = rumps.App("Hello World")
app.run()

print("hey2")