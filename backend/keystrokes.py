from enum import Enum
from typing import List, Tuple

from pynput.keyboard import Key

from ui.kb_controller import KBCntrlrWrapper, KBCntrlCommand

from backend.file_utils import unyaml_thing

config = unyaml_thing('config.yaml')

# if running this on a linux box
IS_LINUX = config['is_linux']
USING_STICKY_KEYS = config['sticky_keys']

MODIFIERS_MAP = {
    'ctrl': Key.ctrl,
    'alt': Key.alt,
    'super': Key.cmd,
    'shift': Key.shift,
}
SPECIAL_OPERAND_KEYS = {
    'tab': Key.tab,
    'left': Key.left,
    'up': Key.up,
    'right': Key.right,
    'down': Key.down,
    'enter': Key.enter,
    'page_down': Key.page_down,
    'page_up': Key.page_up,
    'f1': Key.f1,
    'f2': Key.f2,
    'f3': Key.f3,
    'f4': Key.f4,
    'f5': Key.f5,
    'f6': Key.f6,
    'f7': Key.f7,
    'f8': Key.f8,
    'f9': Key.f9,
    'f10': Key.f10,
    'f11': Key.f11,
    'f12': Key.f12,
    'f13': Key.f13,
    'f14': Key.f14,
    'f15': Key.f15,
    'f16': Key.f16,
    'f17': Key.f17,
    'f18': Key.f18,
    'f19': Key.f19,
    'f20': Key.f20,
}

def parse_hotkey(
        hotkey: str, 
        hotkey_separator: str = '+') -> Tuple[List[Enum], str, bool]:
    """Parses a string specification for a hotkey into usable keys
    
    Given an input like 'ctrl+alt+a', returns a tuple of 
        (Key.ctrl, Key.alt, 'a'). Here, 'a' is the "operand" key. Also, here
        '+' is the hotkey_separator
    
    Args:
        hotkey: the hotkey string specifier, e.g. 'ctrl+alt+a'
        hotkey_separator: the separator character between modifiers and the
            regular key within a single keystroke
    
    Returns:
        a tuple of:
            - a list of modifiers Key.blah (the type of which is an Enum)
            - the string for the "operand" key.
            - a flag indicating if the key was a "special operand", i.e. one 
                of the pyinput keys we have to explicitly map. This has
                implications for later handling.
    """
    # todo: lru cache parse_hotkey()? kinda innefficient to run every time...

    hotkey_keys = hotkey.split(hotkey_separator)
    # modifiers should be at the front
    modifiers = hotkey_keys[:-1]
    operand_key = hotkey_keys[-1]
    
    # make sure they're all unique. we could end up with tricky bugs otherwise
    assert(len(modifiers)) == len(set(modifiers))
    modifiers_obj = [MODIFIERS_MAP[mod] for mod in modifiers]

    assert operand_key not in MODIFIERS_MAP
    # if there is a mapping in special operand keys, get it. otherwise
    # default to it
    if operand_key in SPECIAL_OPERAND_KEYS.keys():
        operand_key_mapped = SPECIAL_OPERAND_KEYS[operand_key]
        was_special_operand = True
    else:
        operand_key_mapped = operand_key
        was_special_operand = False
    return modifiers_obj, operand_key_mapped, was_special_operand

def execute_modified_keystroke(
        kb_controller: KBCntrlrWrapper, hotkey, hotkey_separator: str = '+'):
    """Execute a keystroke with modifiers
    
    We need special handling with modifiers, because there's
    idiosyncratic behavior for pynput when using sticky keys under linux
    
    Args:
        hotkey: see documentation for parse_hotkey()
        kb_controller: the keyboard controller to use to type the keystrokes
        hotkey_separator: see documentation for parse_hotkey()
    """

    modifiers, operand_key, was_special_operand = parse_hotkey(hotkey, hotkey_separator)

    ## press the keys
    # see https://pynput.readthedocs.io/en/latest/keyboard.html
    # WARNING! does not work with sticky keys!
    # unfortunately I couldn't get this to work consistently with sticky
    # keys. Sometimes the modifiers are left engaged, other times not.
    # Behaviour is weird too with multiple modifier keys.
    
    if len(modifiers) > 0:
        last_modifier = modifiers[-1]
    with kb_controller.pressed(*modifiers):
        kb_controller.press(operand_key)
        kb_controller.release(operand_key)

    if IS_LINUX and USING_STICKY_KEYS:
        ## Special handling for sticky keys...
        # if using sticky keys, pyinput exhibits strange behavior from the
        # Xorg system...when using modifiers with non-special keys (like 
        # 'a', '6', or '~' whereas special would include Key.tab and Key.space)
        # not all of the modifiers will be cleared upon keypress of the 
        # operand_key. for whatever reason, the last modifier in the modifiers 
        # list won't be cleared.  we do that explicitly here.
        if len(modifiers) > 0 and not was_special_operand:
            # we start out in sticky "single press" mode...cycle to 
            # sticky latched
            kb_controller.press(KBCntrlCommand('press', last_modifier))
            kb_controller.release(KBCntrlCommand('release', last_modifier))
            # now cycle to "unstuck"
            kb_controller.press(KBCntrlCommand('press', last_modifier))
            kb_controller.release(KBCntrlCommand('release', last_modifier))
