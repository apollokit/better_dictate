import json
import os
from typing import Dict, Any

def unjson_thing(file_path: str = 'thing.json') -> Dict[str, Any]:
    """ Extract a python object from a json file and return it
        
    Args:
        file_path: the file, optionally along with a path to another directory 
        (default: {'thing.json'})
    
    Returns:
        the json as a nested dictionary
    """
    with open(file_path, 'r') as f:
        thing = json.load(f)
    return thing

def json_thing(thing: Dict[str, Any], file_path: str = 'thing.json'):
    """ Store a dictonary (or any other jsonifiable object, really) in a json
    output file
    
    Args:
        thing: the thing to store
        file_path: the file name, optionally along with a path to another 
            directory (default: {'thing.json'})
    """
    thing_dir = os.path.dirname(os.path.realpath(file_path))
    if not os.path.exists(thing_dir):
        os.mkdir(thing_dir)
    with open(file_path, 'w') as f:
        json.dump(thing, f)