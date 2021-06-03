import json
import pickle
import os
from os import path, makedirs
import shutil
from typing import Any, Dict

import yaml  # pylint: disable=import-error


def unyaml_thing(file_path: str = 'thing.yml') -> Dict[str, Any]:
    """ Extract a python object from a yaml file and return it
        
    Args:
        file_path: the file, optionally along with a path to another directory 
        (default: {'thing.yml'})
    
    Returns:
        the yaml as a nested dictionary
    """
    with open(file_path, 'r') as f:
        thing = yaml.safe_load(f)
    return thing


def yaml_thing(thing: Dict[str, Any], file_path: str = 'thing.yml'):
    """ Store a dictonary (or any other yaml object, really) in a yml
    output file
    
    Args:
        thing: the thing to store
        file_path: the file name, optionally along with a path to another 
            directory (default: {'thing.yml'})
    """
    thing_dir = os.path.dirname(os.path.realpath(file_path))
    if not path.exists(thing_dir):
        os.mkdir(thing_dir)
    with open(file_path, 'w') as f:
        yaml.dump(thing, f)


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
    if not path.exists(thing_dir):
        os.makedirs(thing_dir)
    with open(file_path, 'w') as f:
        json.dump(thing, f)


def unpickle_thing(file_path: str = 'thing.pkl') -> Dict[str, Any]:
    """ Extract a python object from a pickle file and return it
        
    Args:
        file_path: the file, optionally along with a path to another directory 
        (default: {'thing.pkl'})
    
    Returns:
        the unpickled thing
    """
    with open(file_path, 'rb') as f:
        thing = pickle.load(f)
    return thing


def pickle_thing(thing: Dict[str, Any], file_path: str = 'thing.pkl'):
    """ Store a dictonary (or any other picklable object, really) in a pickle
    output file

    Args:
        thing: the thing to store
        file_path: the file name, optionally along with a path to another 
            directory (default: {'thing.pkl'})
    """
    thing_dir = os.path.dirname(os.path.realpath(file_path))
    if not path.exists(thing_dir):
        os.mkdir(thing_dir)
    with open(file_path, 'wb') as f:
        pickle.dump(thing, f)


def mkdir_safe(the_dir: str):
    """ Make a directory, checking first if it already exists
    
    Args:
        the_dir: the directory
    """
    if not path.exists(the_dir):
        makedirs(the_dir)


def rmtree_safe(the_dir: str):
    """ Delete a directory and everything under it, checking first if it
    actually exists
    
    Args:
        the_dir: the directory
    """
    if path.exists(the_dir):
        shutil.rmtree(the_dir)


def mkdir_empty(the_dir: str):
    """Make directory the_dir, blowing away anything that might already exist at
    that location
    
    Args:
        the_dir: the directory
    """
    rmtree_safe(the_dir)
    makedirs(the_dir)
