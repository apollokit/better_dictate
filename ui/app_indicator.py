#!/usr/bin/python
#
# see:
# https://lazka.github.io/pgi-docs/AppIndicator3-0.1/classes/Indicator.html

#pylint: disable=wrong-import-position
from os import path
import time

import gi
gi.require_version('Gtk', '3.0') 
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk as gtk, AppIndicator3 as appindicator

from backend.manager import app_mngr
from backend.executor import executor_inst
#pylint: enable=wrong-import-position

abs_file_dir = path.dirname(path.abspath(__file__))

# Icon paths
# this has to be absolute...
# use bad pun boy for the time being :bad_pun:
active_icon = path.join(abs_file_dir, '..', 'sandbox', 'bad_pun_boy.png')
sleeping_icon = path.join(abs_file_dir, '..', 'sandbox', 'bad_pun_boy_evil.png')

## Menu interaction handler functions

def do_quit(_):
    """Handle quit
    """
    app_mngr.signal_quit()
    gtk.main_quit()


def reload_commands(_):
    """Reload commands into the dictate parser
    """
    executor_inst.reload_commands()

## Setup menu and app indicator

def menu() -> gtk.Menu:
    """Make the gtk menu
    
    Returns:
        the menu
    """
    the_menu = gtk.Menu()

    menu_quit = gtk.MenuItem(label='Quit')
    menu_quit.connect('activate', do_quit)
    the_menu.append(menu_quit)
    
    menu_reload = gtk.MenuItem(label='Reload commands')
    menu_reload.connect('activate', reload_commands)
    the_menu.append(menu_reload)

    the_menu.show_all()
    return the_menu

# see here for some docs:
# https://wiki.ubuntu.com/DesktopExperienceTeam/ApplicationIndicators
_indicator = appindicator.Indicator.new("customtray", 
    active_icon,
    appindicator.IndicatorCategory.APPLICATION_STATUS)
_indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
_indicator.set_menu(menu())
# _indicator.set_label(' test', '')


## Threads

def app_indicator_thread():
    """Thread function that handles updating the app system tray icon    
    """

    while True:        
        # set label on the _indicator
        # _indicator.set_label(f' yo {counter}', '')

        # protect against quitting condition before doing anything with the
        # app _indicator. This is to avoid any race conditions with gtk
        # shutting down
        if app_mngr.quitting:
            # break the loop if we're quitting
            break

        # set the app icon depending on whether we're sleeping or not
        if app_mngr.sleeping:
            # second argument is apparently a description for
            # accessibility in the GUI
            _indicator.set_icon_full(sleeping_icon, \
                'BetterDictate is sleeping')
        else:
            _indicator.set_icon_full(active_icon, \
                'BetterDictate is active')

        time.sleep(0.01)

# also have to run this thread. It's the background thing that actually
# manages the UI
gtk_main_thread = gtk.main