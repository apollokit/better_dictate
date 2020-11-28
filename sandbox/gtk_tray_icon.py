#!/usr/bin/python
# modified from: https://fosspost.org/custom-system-tray-icon-indicator-linux/
#
# requirements:
# pip install PyGObject
# sudo apt-get install gir1.2-appindicator3
#
# see:
# https://lazka.github.io/pgi-docs/AppIndicator3-0.1/classes/Indicator.html

from concurrent.futures import ThreadPoolExecutor, as_completed
import gi
gi.require_version('Gtk', '3.0') 
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk as gtk, AppIndicator3 as appindicator
import os
from os import path
import threading
import time

yo_event = threading.Event()
quit_event = threading.Event()

file_dir = path.dirname(path.abspath(__file__))

def note(_):
    os.system("gedit $HOME/Documents/notes.txt")

def yo_command(_):
    yo_event.set()

def quit(_):
    gtk.main_quit()
    quit_event.set()

def menu():
    menu = gtk.Menu()

    command_one = gtk.MenuItem(label='My Notes')
    command_one.connect('activate', note)
    menu.append(command_one)
    
    command_yo = gtk.MenuItem(label='Yo')
    command_yo.connect('activate', yo_command)
    menu.append(command_yo)

    exittray = gtk.MenuItem(label='Exit Tray')
    exittray.connect('activate', quit)
    menu.append(exittray)

    menu.show_all()
    return menu

# this has to be absolute...
iconpath = path.join(file_dir, 'bad_pun_boy.png')
iconpath2 = path.join(file_dir, 'bad_pun_boy_evil.png')

# see here for some docs:
# https://wiki.ubuntu.com/DesktopExperienceTeam/ApplicationIndicators
indicator = appindicator.Indicator.new("customtray", 
    iconpath,
    appindicator.IndicatorCategory.APPLICATION_STATUS)
indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
indicator.set_menu(menu())
indicator.set_label(' test', '')

def yo_thread():
    counter = 0
    first_icon = True
    while True:
        if yo_event.is_set():
            counter += 1
            
            print("yo")
            # set label on the indicator
            indicator.set_label(f' yo {counter}', '')
            
            # flip the icon
            first_icon = not first_icon
            if first_icon:
                indicator.set_icon_full(iconpath, 'accessibility description')
            else:
                indicator.set_icon_full(iconpath2, 'accessibility description')

            yo_event.clear()
        if quit_event.is_set():
            break
        time.sleep(0.01)


if __name__ == "__main__":

    # note that shutdown event can be invoked from keyboard.py
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        futures.append(executor.submit(
            gtk.main))
        futures.append(executor.submit(
            yo_thread))
