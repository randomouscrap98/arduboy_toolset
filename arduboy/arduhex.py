from arduboy.constants import *

import logging
import os
import tempfile
import zipfile
import demjson3

from typing import List
from dataclasses import dataclass, field
from PIL import Image

# Represents maximum data pulled from SOME kind of sketch file
@dataclass
class ArduboyParsed:
    original_filename: str
    rawhex: str = field(default="")

    # I believe all of this could be stored in a .arduboy file.
    # TODO: go research the format of arduboy zip files!
    title: str = field(default="")
    version: str = field(default="")
    developer: str = field(default="")
    info: str = field(default="")
    image: Image = field(default=None)
    data_raw: bytearray = field(default_factory=lambda:bytearray())
    save_raw: bytearray = field(default_factory=lambda:bytearray())

    def __str__(self) -> str:
        return f"{self.original_filename}"

# Represents a parsed arduboy hex file. Not sure if it's really necessary tbh...
@dataclass 
class ArduhexParsed:
    arduboy_data: ArduboyParsed
    flash_data: bytearray = field(default_factory=lambda: bytearray(b'\xFF' * FLASHSIZE))
    flash_page_count: int = field(default=0)
    flash_page_used: List[bool] = field(default_factory=lambda: [False] * 256)
    overwrites_caterina: bool = field(default=False)


# Try to get the given image in the right format and size for Arduboy. Still returns a PIL image. This is 
def pilimage_titlescreen(image):
    # Actually for now I'm just gonna stretch it, I don't care! Hahaha TODO: fix this
    image = image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.NEAREST)
    image = image.convert("1") # Do this after because it's probably better AFTER nearest neighbor
    return image

# Read raw data from the arduboy or hex file. Return an intermediate representation
# which has as much data as possible filed in.
def read(filepath) -> ArduboyParsed:
    result = ArduboyParsed(os.path.splitext(os.path.basename(filepath))[0])
    try:
        # First, we try to open the file as a zip. This apparently handles both .zip and .arduboy
        # files; this is how Mr.Blink's arduboy python utilities works (mostly)
        with zipfile.ZipFile(filepath) as zip_ref:
            logging.debug(f"Input file {filepath} is zip archive, scanning for hex file")
            # Create a temporary directory to hold the files we extract temporarily
            with tempfile.TemporaryDirectory() as temp_dir:
                def extract(fn): # Simple function to extract a file, it's always the same
                    zip_ref.extract(fn, temp_dir)
                    extract_file = os.path.join(temp_dir, fn)
                    logging.debug(f"Reading arduboy archive file {extract_file} (taken from archive into temp file)")
                    return extract_file
                for filename in zip_ref.namelist():
                    if filename.lower().endswith(".hex"):
                        extract_file = extract(filename)
                        with open(extract_file,"r") as f: # The arduboy utilities opens with just "r", no binary flags set.
                            result.rawhex = f.read()
                    elif filename.lower() == "info.json":
                        try:
                            extract_file = extract(filename)
                            info = demjson3.decode_file(extract_file, encoding="utf-8", strict=False)
                            if "title" in info: result.title = info["title"]
                            if "author" in info: result.developer = info["author"]
                            if "description" in info: result.info = info["description"]
                            if "version" in info: result.version = info["version"]
                        except Exception as ex:
                            logging.warning(f"Couldn't load info.json: {ex} (ignoring)")
                    elif filename.lower().endswith(".png") and filename.lower() != "banner.png" and not result.image:
                        try:
                            extract_file = extract(filename)
                            result.image = pilimage_titlescreen(Image.open(extract_file))
                        except Exception as ex:
                            logging.warning(f"Couldn't load title image: {ex} (ignoring)")
                    elif filename.lower() == "fxdata.bin":
                        extract_file = extract(filename)
                        with open(extract_file, "rb") as f:
                            result.data_raw = f.read()
                    elif filename.lower() == "fxsave.bin":
                        extract_file = extract(filename)
                        with open(extract_file, "rb") as f:
                            result.save_raw = f.read()

            if not result.rawhex:
                raise Exception("No .hex file read from arduboy file!")
    except:
        logging.debug(f"Reading potential hex file {filepath} (validating later)")
        with open(filepath,"r") as f:
            result.rawhex = f.read()
    return result

# Parse pages and data relevant for flashing out of the parsed arduboy file
# Throws an exception if the records can't be validated. Taken almost verbatim from 
# https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/uploader.py
def parse(arduboy_data: ArduboyParsed):
    logging.debug(f"Parsing arduboy data {arduboy_data}")
    result = ArduhexParsed(arduboy_data)
    records = arduboy_data.rawhex.splitlines()
    flash_addr = 0
    for rcd in records :
        # Assuming this is some kind of end symbol
        if rcd == ":00000001FF": 
            break
        elif rcd[0] == ":" :
            # This part is literally just copy + paste, the hex format seems complicated...
            rcd_len  = int(rcd[1:3],16)
            rcd_typ  = int(rcd[7:9],16)
            rcd_addr = int(rcd[3:7],16)
            rcd_sum  = int(rcd[9+rcd_len*2:11+rcd_len*2],16)
            if (rcd_typ == 0) and (rcd_len > 0) :
                flash_addr = rcd_addr
                result.flash_page_used[int(rcd_addr / 128)] = True
                result.flash_page_used[int((rcd_addr + rcd_len - 1) / 128)] = True
                checksum = rcd_sum
                for i in range(1,9+rcd_len*2, 2) :
                    byte = int(rcd[i:i+2],16)
                    checksum = (checksum + byte) & 0xFF
                    if i >= 9:
                        result.flash_data[flash_addr] = byte
                        flash_addr += 1
                if checksum != 0:
                    raise Exception(f"Hex file contains errors! Checksum fail: {checksum}")
    # Now count the pages and see if "caterina" (whatever that means). Note: You CANNOT simplify
    # this into some simple array.count method! The check is if the flash page is used AND if it 
    # goes beyond a certain threshold!
    for i in range (256) :
        if result.flash_page_used[i] :
            result.flash_page_count += 1
            if i >= 224 :
                result.overwrites_caterina = True

    return result
