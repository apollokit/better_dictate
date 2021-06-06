# better_dictate
A tool for general purpose dictation on a desktop box

## Installation

### All Platforms

- `cd better_dictate/env`
- `./create_virtualenv.sh`

### MacOS Specific

- Install PyGObject per instructions [here](https://pygobject.readthedocs.io/en/latest/getting_started.html#macosx-logo-macos)
    - Install Apple Command Line Tools: `xcode-select --install`
    - `brew install pygobject3 gtk+3`

## Execution

- In one terminal window:
    - `cd better_dictate`
    - `./run.sh`
- In a second terminal window:
    - `cd better_dictate/frontend`
    - `./run.sh`