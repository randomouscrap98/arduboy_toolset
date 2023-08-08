import logging
import os
import tempfile
import zipfile

from arduboy.constants import *
from typing import List
from dataclasses import dataclass, field

# Represents maximum data pulled from SOME kind of sketch file
@dataclass
class ArduboyParsed:
    original_filename: str
    rawhex: str = field(default="")
    # Add other possible fields pulled from Arduboy files

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


# Read raw data from the arduboy or hex file. Return an intermediate representation
# which has as much data as possible filed in.
def read(filepath) -> ArduboyParsed:
    result = ArduboyParsed(os.path.splitext(os.path.basename(filepath))[0])
    try:
        # First, we try to open the file as a zip. This apparently handles both .zip and .arduboy
        # files; this is how Mr.Blink's arduboy python utilities works (mostly)
        with zipfile.ZipFile(filepath) as zip_ref:
            logging.debug(f"Input file {filepath} is zip archive, scanning for hex file")
            for filename in zip_ref.namelist():
                if filename.lower().endswith(".hex"):
                    # Create a temporary directory to hold the file (and other contents maybe later)
                    with tempfile.TemporaryDirectory() as temp_dir:
                        zip_ref.extract(filename, temp_dir)
                        extract_file = os.path.join(temp_dir, filename)
                        # The arduboy utilities opens with just "r", no binary flags set.
                        logging.debug(f"Reading hex file {extract_file} (taken from archive into temp file, validating later)")
                        with open(extract_file,"r") as f:
                            result.rawhex = f.read()
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
