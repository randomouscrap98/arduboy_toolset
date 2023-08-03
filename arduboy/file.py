# NOTE: a lot of this code is taken from
# https://github.com/MrBlinky/Arduboy-Python-Utilities

import zipfile
import tempfile
import os
import logging
from dataclasses import dataclass, field
from typing import List

FLASHSIZE=32768
LCDBOOTPROGRAM = b"\xD5\xF0\x8D\x14\xA1\xC8\x81\xCF\xD9\xF1\xAF\x20\x00"

# Read so-called "records" (lines) from the given arduboy or hex file. No parsing or verification is done yet.
def read_arduhex(filepath):
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
                            return f.readlines()
    except:
        logging.debug(f"Reading potential hex file {filepath} (validating later)")
        with open(filepath,"r") as f:
            return f.readlines()

@dataclass 
class ArduhexParsed:
    flash_addr: int = field(default=0)
    flash_data: bytearray = field(default_factory=lambda: bytearray(b'\xFF' * FLASHSIZE))
    flash_page: int = field(default=1)
    flash_page_count: int = field(default=0)
    flash_page_used: List[bool] = field(default_factory=lambda: [False] * 256)
    is_caterina: bool = field(default=False)

    # Taken almost directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/uploader.py.
    # NO PROTECTION AGAINST MULTIPLE CALLS!
    def patch_ssd1309(self):
        lcdBootProgram_addr = self.flash_data.find(LCDBOOTPROGRAM)
        if lcdBootProgram_addr >= 0:
            self.flash_data[lcdBootProgram_addr+2] = 0xE3;
            self.flash_data[lcdBootProgram_addr+3] = 0xE3;
            return True
        else:
            return False

    # Taken directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/uploader.py
    # NO PROTECTION AGAINST MULTIPLE CALLS!
    def patch_microled(self):
        for i in range(0,FLASHSIZE-4,2):
            if self.flash_data[i:i+2] == b'\x28\x98':   # RXLED1
                self.flash_data[i+1] = 0x9a
            elif self.flash_data[i:i+2] == b'\x28\x9a': # RXLED0
                self.flash_data[i+1] = 0x98
            elif self.flash_data[i:i+2] == b'\x5d\x98': # TXLED1
                self.flash_data[i+1] = 0x9a
            elif self.flash_data[i:i+2] == b'\x5d\x9a': # TXLED0
                self.flash_data[i+1] = 0x98
            elif self.flash_data[i:i+4] == b'\x81\xef\x85\xb9' : # Arduboy core init RXLED port
                self.flash_data[i] = 0x80
            elif self.flash_data[i:i+4] == b'\x84\xe2\x8b\xb9' : # Arduboy core init TXLED port
                self.flash_data[i+1] = 0xE0

# Parse relevant information out of the arduboy file's "records" (the result of read_basic_arduboy).
# Throws an exception if the records can't be validated. Taken almost verbatim from 
# https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/uploader.py
def parse_arduhex(records):
    logging.debug(f"Parsing hex file with {len(records)} records")
    result = ArduhexParsed()
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
                result.flash_addr = rcd_addr
                result.flash_page_used[int(rcd_addr / 128)] = True
                result.flash_page_used[int((rcd_addr + rcd_len - 1) / 128)] = True
                checksum = rcd_sum
                for i in range(1,9+rcd_len*2, 2) :
                    byte = int(rcd[i:i+2],16)
                    checksum = (checksum + byte) & 0xFF
                    if i >= 9:
                        result.flash_data[result.flash_addr] = byte
                        result.flash_addr += 1
                if checksum != 0:
                    raise Exception(f"Hex file contains errors! Checksum fail: {checksum}")
    # Now count the pages and see if "caterina" (whatever that means)
    for i in range (256) :
        if result.flash_page_used[i] :
            result.flash_page_count += 1
            if i >= 224 :
                result.is_caterina = True

    return result
