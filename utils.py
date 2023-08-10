import arduboy.fxcart

from constants import *
from arduboy.constants import *

import os
import time
import textwrap
import slugify
import logging

from PIL import Image, ImageDraw, ImageFont

def get_filesafe_datetime():
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())

def get_sketch_backup_filename():
    return f"sketch-backup-{get_filesafe_datetime()}.bin"

def get_eeprom_backup_filename():
    return f"eeprom-backup-{get_filesafe_datetime()}.bin"

def get_fx_backup_filename():
    return f"fx-backup-{get_filesafe_datetime()}.bin"

def get_meta_backup_filename(meta, extension):
    return slugify.slugify(meta.title if meta.title else "") + f"_{get_filesafe_datetime()}.{extension}"

def resource_file(name):
    basedir = os.path.dirname(__file__)
    return os.path.join(basedir, 'appresource', name)

# Create a default titlescreen using the given text. We use our little font we got from the internet (free to use, attribution given)
def make_titlescreen(text):
    img = Image.new('1', (SCREEN_WIDTH, SCREEN_HEIGHT), 0)  # 1-bit black and white image
    font = ImageFont.truetype(resource_file(TINYFONT), 16) # I think the thing said 16, 32, etc
    draw = ImageDraw.Draw(img)
    # We know each character takes up a fixed amount of pixels, so this works.
    wrapped_text = textwrap.fill(text, width=((SCREEN_WIDTH - 8)//TINYFONT_WIDTH))  
    _, _, text_width, text_height = draw.textbbox((0,0), wrapped_text, font=font)

    # Calculate text position to center it in the image
    x = (SCREEN_WIDTH - text_width) // 2
    y = (SCREEN_HEIGHT - text_height) // 2

    # Draw the wrapped text in white color
    draw.text((x, y), wrapped_text, font=font, fill=1)

    return img

def make_titlescreen_from_slot(slot: arduboy.fxcart.FxParsedSlot):
    logging.debug(f"Creating title image for {slot.meta.title}")
    base = "Category: " if slot.is_category() else "Game: "
    if slot.meta.title:
        return make_titlescreen(f"{base}{slot.meta.title}")
    else:
        return make_titlescreen(f"{base}{slot.category}")
