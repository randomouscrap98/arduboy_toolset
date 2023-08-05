# Arduboy toolset

A set of personal tools derived heavily from https://github.com/MrBlinky/Arduboy-Python-Utilities
made as a learning exercise. I wanted to understand what makes Arduboy tick, while also maybe
providing a slightly easier way to manage Arduboy. 

## Running

If you have a release version, just run `arduboy_toolset.exe` to get a GUI.

If you have python already and just want to run from source, or want to run the command line 
(clone repo first ofc):

```shell
cd arduboy_toolset
# Optional: create and activate a virtual environment
# python -m venv .venv
# source .venv/bin/activate
pip install -r requirements.txt
python main_cli.py
# Or for gui, use main_gui.py
```

## Creating a standalone

This has to be done for each operating system, there is no cross compiler. Note that because of weird 
nonsense with Windows, I have to build the CLI and the GUI separately.

```shell
cd arduboy_toolset
# Optional: create and activate a virtual environment
# python -m venv .venv
# source .venv/bin/activate
pip install -r requirements.txt
pyinstaller arduboy_toolset_cli.spec
pyinstaller arduboy_toolset.spec
mv dist/arduboy_toolset_cli dist/arduboy_toolset
mv dist/arduboy_tooset/arduboy_toolset dist/arduboy_toolset/
```

Notes: 
- The GUI is a "onefile" app, it will startup slower but you can take that single file
  and put it anywhere.
- The GUI has the console removed; this is the main reason for having a separate GUI
  and CLI application
- The CLI application, to increase startup speed (because of how it might be used),
  requires all files in that folder (other than the GUI)
- The icon HAS to be a .ico file for windows

## Plans
- Get releases for linux, windows, and macOS (I don't have a mac yet though)
- Get a relatively robust GUI that has most of the options from the command line
- Create a more manageable cart builder (personal: not meant to replace existing cart system at all)
