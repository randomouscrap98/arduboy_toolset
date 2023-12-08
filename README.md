# Arduboy toolset

<p float="left">
<img alt="Main window" src="https://github.com/randomouscrap98/arduboy_toolset/blob/main/appresource/screenshot_tools_main.png?raw=true" height=250>
<img alt="Cart builder" src="https://github.com/randomouscrap98/arduboy_toolset/blob/main/appresource/screenshot_cartbuilder_main.png?raw=true" height=250>
</p>
<p float="left">
<img alt="Package editor" src="https://github.com/randomouscrap98/arduboy_toolset/blob/main/appresource/screenshot_package_main.png?raw=true" height=250>
<img alt="Image converter" src="https://github.com/randomouscrap98/arduboy_toolset/blob/main/appresource/screenshot_imageconvert_main.png?raw=true" height=250>
</p>

A set of personal tools derived heavily from https://github.com/MrBlinky/Arduboy-Python-Utilities. 
This is a fan project and not an official too, use at your own risk (see license).

The toolset allows you to:
* Upload and backup sketches + eeprom
* Upload and backup FX flash data (carts of games)
* Add/update games in the flashcart of your Arduboy (FX or otherwise)
* Create/edit custom flashcarts with custom categories
* Create/edit `.arduboy` package files
* Convert images into code or data for use with the Arduboy2 or FX library
* Update your Arduboy FX with the latest games and updates from the [official cart website](http://www.bloggingadeadhorse.com/cart/Cart.html)

## Quickstart

* Get the latest release from https://github.com/randomouscrap98/arduboy_toolset/releases. 
* For **Windows**: just run the exe
* For **MacOS** (requires a modern version, sorry!): mount the `.dmg` and run the tool directly from within. There is no installer
* For **Linux**, you probably need to add yourself to a dialout group, or run the program as sudo:
  * `sudo usermod -a -G dialout <username>`, just once
  * There are no releases for Linux. Clone the repo (or download the source from release) and if you're 
    unsure, just run `sh linux_easyrun.sh`. Feel free to modify the script if you don't like it! All requirements 
    are satisfied by pip and python 3.8 or greater

The first window is the basic toolset, letting you upload and download stuff from your Arduboy. Most of the tools
are here, including the `.arduboy` package creator and image converter.

If you want to add or update games on your Arduboy FX, use the `File` menu to open the cart builder. From here, you 
can use the newly opened window's `File` menu to read the FX cart off your Arduboy FX. It will take sometime to load.
Once it's complete, you can browse the **local copy** of your FX games in the window. Changes you make here are not 
immediately put onto your Arduboy. 

You can add games by dragging and dropping `.hex` or `.arduboy` files into the window. They will be inserted below
the currently focused menu item. If you accidently place a game where you don't want it, you can drag the games around
in the list, or press `Ctrl-delete` or use the `Cart` menu to remove them. When you're ready to put everything back on 
your Arduboy, use the `File` menu again to `Flash to Arduboy`. 

Get the latest games by using the `Network` menu to update your cart. This connects to the offical cart website
and calculates which games you're missing and which need an update. **WARNING:** there are no unique identifiers for
games, so a best attempt is made to match games against the official cart website, but it can get it wrong! Always
check the update window for correctness before applying the update!

## Caveats

While I've done as much as I can to ensure the tool works appropriately, I can't promise it will work flawlessly,
I don't take any responsibility for lost data (I'm sorry!). 

### Prince of Arabia + other FX titles, 2023

Using the Cart Editor will usually preserve the FX saves used by the more complex "FX" games, such as 
[Prince Of Arabia](https://github.com/Press-Play-On-Tape/PrinceOfArabia). However, we've found that sometimes
the carts were not configured properly from the cart builder website, and your save data may be located in the
development area at the end of the flashcart. As such, there is a chance that updating your cart will
make you lose this save. You can check if your Prince of Arabia game is correct by loading the cart in
the cart builder, using `Ctrl-F` to search for `Arabia`, then checking the 3 numbers under the game's 
title image on the left. If the last number is **4096 or higher**, your game is **correct**. If it's 0, it is
development mode and you may lose the save.

If you wish to backup a "Development" save, you will need to make a **complete** backup of your FX, without trimming.
The Arduboy toolset defaults to trimming the FX backup, just uncheck the trim option before you backup you flash and
the save data will be included. This is because the save is stored at the very end of the cart, so trimming the backup
would remove that part from the file.


## Running From Source

If you have python already and just want to run from source, or want to run the command line 
(clone repo first ofc):

```shell
cd arduboy_toolset
# Optional: create and activate a virtual environment
# python -m venv .venv
# source .venv/bin/activate
pip install -r requirements.txt
python main_gui.py
# You can also run the cart builder directly (anything named main_* can be run directly)
python main_cart.py
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
pyinstaller arduboy_toolset.spec
# For MacOS, need to then package it into a dmg (command will be added later)
```

## Notes: 
- There used to be a CLI app, and the code is still there if you want to use it, but I'm no longer
  supporting it. I plan on making a separate, far more robust CLI
- The GUI is a "onefile" app, it will startup slower but you can take that single file
  and put it anywhere. This may change in the future to increase startup time
- The GUI has the console removed; if you're looking for logs, the program logs
  to a txt file next to the executable
- Windows will often mark it as some kind of "dangerous file". Please see 
  https://github.com/pyinstaller/pyinstaller/issues/5854