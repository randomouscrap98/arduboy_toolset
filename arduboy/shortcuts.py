from hashlib import sha256
import logging
import arduboy.arduhex
import arduboy.fxcart

from arduboy.common import *
from arduboy.constants import *

# NOTE: this is strictly higher level than any other file! Do NOT include this in any 
# arduboy library files, it is specifically for external use!

def new_parsed_slot_from_category(title, info = "", image = None, category_id = 0):
    return arduboy.fxcart.FxParsedSlot(
        category_id,
        image,
        bytearray(),
        bytearray(),
        bytearray(),
        arduboy.fxcart.FxSlotMeta(title, "", "", info)
    )
    # sha256(bytearray()).digest(),

# Given a parsed arduhex file, generate a reasonable slot file
def new_parsed_slot_from_arduboy(parsed: arduboy.arduhex.ArduboyParsed):
    return arduboy.fxcart.FxParsedSlot(
        0, # Might not matter
        pilimage_to_bin(parsed.image) if parsed.image else None, # We are hoping the format of the image is already correct!
        arduboy.fxcart.arduhex_to_bin(parsed.rawhex), # The three main slot data fields are all stored raw in FxParsedSlot, including program.
        parsed.data_raw,
        parsed.save_raw,
        arduboy.fxcart.FxSlotMeta(parsed.title if parsed.title else parsed.original_filename, parsed.version, parsed.developer, parsed.info)
    )
