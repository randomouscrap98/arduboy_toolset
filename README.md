# Arduboy toolset (not official)

I just wanted to learn about Arduboy by making some of the existing tools.
There are better tools to use (such as
https://github.com/MrBlinky/Arduboy-Python-Utilities). I recommend using those
instead.

## What tools?

I plan on having:
- A .hex and .arduboy flasher
- A bin flasher for the FX memory
- Something to save and restore the eeprom
- Something to save/restore the flash and fx mem
- A cart builder (using all local files in a custom format, not the existing .csv format)
- perhaps a way to "reverse engineer" an existing bin file so it is easier to simply "add" games to an existing cart
  (depends on complexity)

## Caveats
- I can't seem to build purely statically linked (using musl). I may have to build for glibc, or have people build from source.
  - This is apparently normal: they say specifically that the glibc version links against the external library libudev, and not
    including that (which I assume is removed for the static linked musl build)
- If I can't get the windows build to recognize the arduboy then this project is dead in the water utnil I figure that out

