from hashlib import sha256
import logging
import arduboy.arduhex
import arduboy.fxcart

from arduboy.common import *
from arduboy.constants import *

from PIL import Image

# NOTE: this is strictly higher level than any other file! Do NOT include this in any 
# arduboy library files, it is specifically for external use!

def new_parsed_slot_from_category(title: str, info : str = "", image : Image = None, category_id : int = 0) -> arduboy.fxcart.FxParsedSlot:
    return arduboy.fxcart.FxParsedSlot(
        category_id,
        pilimage_to_bin(image) if image else None, # MUST BE none for things to know there's no image!
        bytearray(),
        bytearray(),
        bytearray(),
        arduboy.fxcart.FxSlotMeta(title, "", "", info)
    )
    # sha256(bytearray()).digest(),

# Given a parsed arduhex file, generate a reasonable slot file
def new_parsed_slot_from_arduboy(parsed: arduboy.arduhex.ArduboyParsed) -> arduboy.fxcart.FxParsedSlot:
    return arduboy.fxcart.FxParsedSlot(
        0, # Might not matter
        pilimage_to_bin(parsed.image) if parsed.image else None, # MUST BE none for things to know there's no image!
        arduboy.fxcart.arduhex_to_bin(parsed.rawhex), # The three main slot data fields are all stored raw in FxParsedSlot, including program.
        parsed.data_raw,
        parsed.save_raw,
        arduboy.fxcart.FxSlotMeta(parsed.title if parsed.title else parsed.original_filename, parsed.version, parsed.developer, parsed.info)
    )
