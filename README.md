# Arduboy toolset

A set of personal tools derived heavily from https://github.com/MrBlinky/Arduboy-Python-Utilities
made as a learning exercise. I wanted to understand what makes Arduboy tick, while also maybe
providing a slightly easier way to manage Arduboy. 

## Running

If you have python already and just want to run from source (clone repo first ofc):

```shell
cd arduboy_toolset
# Optional: create and activate a virtual environment
# python -m venv .venv
# source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Creating a standalone

This has to be done for each operating system, there is no cross compiler

```shell
cd arduboy_toolset
# Optional: create and activate a virtual environment
# python -m venv .venv
# source .venv/bin/activate
pip install -r requirements.txt
pyinstaller --onefile --name arduboy_toolset main.py
```

## Plans
- Get releases for linux, windows, and macOS (I don't have a mac yet though)
- Get a relatively robust GUI that has most of the options from the command line
- Create a more manageable cart builder (personal: not meant to replace existing cart system at all)
