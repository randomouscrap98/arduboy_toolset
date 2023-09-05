"""
Functions and classes related to Arduboy sketches and hex files, which I've dubbed "Arduhex". 
"""

from .constants import *
from .common import *

import logging
import os
import tempfile
import zipfile
import demjson3
import binascii
import slugify

from pathlib import Path
from typing import List
from dataclasses import dataclass, field
from PIL import Image

"""Number of default bytes per record when writing a .hex file"""
BYTES_PER_RECORD = 16

DEVICE_ARDUBOY = "Arduboy"
DEVICE_ARDUBOYFX = "ArduboyFX"
DEVICE_ARDUBOYMINI = "ArduboyMini"
DEVICE_UNKNOWN = "Unknown"


@dataclass
class ArduboyBinary:
    """A single "binary" field from a .arduboy file"""
    device: str = field(default="")
    rawhex: str = field(default="")
    data_raw: bytearray = field(default_factory=lambda:bytearray())
    save_raw: bytearray = field(default_factory=lambda:bytearray())


@dataclass
class ArduboyParsed:
    """Represents as much data as possible pulled from either a .arduboy file or a .hex sketch.
    
    Only fields which were found will be set; all fields have reasonable defaults.
    """
    original_filename: str

    binaries: List[ArduboyBinary] = field(default_factory=lambda: [])
    # rawhex: str = field(default="")

    # I believe all of this could be stored in a .arduboy file.
    # TODO: go research the format of arduboy zip files!
    title: str = field(default="")
    version: str = field(default="")
    developer: str = field(default="")
    info: str = field(default="")
    image: Image = field(default=None)
    # data_raw: bytearray = field(default_factory=lambda:bytearray())
    # save_raw: bytearray = field(default_factory=lambda:bytearray())

    # Some optional fields
    date : str = field(default=None)
    genre : str = field(default=None)
    publisher : str = field(default=None)
    idea : str = field(default=None)
    code : str = field(default=None)
    art : str = field(default=None)
    sound : str = field(default=None)
    url : str = field(default=None)
    sourceUrl : str = field(default=None)
    email : str = field(default=None)
    companion : str = field(default=None)

    def __str__(self) -> str:
        return f"{self.original_filename}"
    
    def _fill_generic(info, func):
        """Using given function, assign fields from a .arduboy item into a ArduboyParsed object
        
        In other words, this function represents the mapping between .arduboy json and the ArduboyParsed 
        fields. If you construct a function which takes a json object, the json field, and the ArduboyParsed
        field, you could pass that to this function to run it on all field associations.
        """
        func(info, "title")
        func(info, "author", "developer")
        func(info, "description", "info")
        func(info, "version")
        func(info, "genre")
        func(info, "date")
        func(info, "publisher")
        func(info, "idea")
        func(info, "code")
        func(info, "art")
        func(info, "sound")
        func(info, "url")
        func(info, "sourceUrl")
        func(info, "email")
        func(info, "companion")

    
    def fill_with_info(self, info):
        """Fill self with the info given. In other words, convert info json into a ArduboyParsed"""
        ArduboyParsed._fill_generic(info, self._set_self)

    def fill_info(self, info):
        """Fill info with data from self. In other words, convert ArduboyParsed into info json"""
        ArduboyParsed._fill_generic(info, self._set_info)
    
    def _set_self(self, info, field, prop = None):
        if not prop:
            prop = field
        if field in info:
            setattr(self, prop, info[field])
        return getattr(self, prop)
    
    def _set_info(self, info, field, prop = None):
        if not prop:
            prop = field
        value = getattr(self, prop)
        if value is not None:
            info[field] = value
        return value


@dataclass 
class ArduhexParsed:
    """Represents a parsed arduboy hex file. This probably isn't necessary and may be removed in the future"""
    arduboy_data: ArduboyParsed
    flash_data: bytearray = field(default_factory=lambda: bytearray(b'\xFF' * FLASHSIZE))
    flash_page_count: int = field(default=0)
    flash_page_used: List[bool] = field(default_factory=lambda: [False] * 256)
    overwrites_caterina: bool = field(default=False)

    def flash_data_min(self):
        """Get the minimal slice of data which actually houses used pages (i.e. a trim)"""
        return self.flash_data[:FLASH_PAGESIZE * self.flash_page_count]


def read(filepath: str) -> ArduboyParsed:
    """Read some kind of sketch file, whether .arduboy or .hex, and parse into an intermediate representation.
    
    Note: only fields which could be read or computed are filled in. Unlike previous versions, this
    uses the extension to determine how to load.
    """
    path = Path(filepath)
    if path.suffix == ".arduboy":
        return read_arduboy(filepath)
    elif path.suffix == ".hex":
        return read_hex(filepath)
    else:
        raise Exception(f"Unknown file format: {path.suffix}")

def read_hex(filepath: str, device: str = DEVICE_UNKNOWN) -> ArduboyParsed:
    """Read a single hex file as a full ArduboyParsed object. Most fields will be unset"""
    logging.debug(f"Reading data from hex file: {filepath}")
    result = ArduboyParsed(Path(filepath).stem)
    with open(filepath,"r") as f:
        binary = ArduboyBinary(device = device, rawhex = f.read())
        result.binaries.append(binary)
    return result

def read_arduboy(filepath: str) -> ArduboyParsed:
    """Read an entire arduboy file, pulling as much data as possible out of it.
    
    Note: info.json must exist, and binaries must be described using the 'binaries' array in info.json
    """
    logging.debug(f"Reading data from arduboy file: {filepath}")
    result = ArduboyParsed(Path(filepath).stem)
    with zipfile.ZipFile(filepath) as zip_ref:
        # Create a temporary directory to hold the files we extract temporarily
        with tempfile.TemporaryDirectory() as temp_dir:
            def extract(fn): # Simple function to extract a file, it's always the same
                zip_ref.extract(fn, temp_dir)
                extract_file = os.path.join(temp_dir, fn)
                logging.debug(f"Reading arduboy archive file {extract_file} (taken from archive into temp file)")
                return extract_file
            extract_file = extract("info.json")
            info = demjson3.decode_file(extract_file, encoding="utf-8", strict=False)
            result.fill_with_info(info)
            # Now we must go manually extract some files! Binaries are a complicated business!
            if "binaries" in info:
                for binary in [x for x in info["binaries"] if "title" in x]:
                    title = binary["title"]
                    if "filename" not in binary:
                        raise Exception(f"No filename set for binary '{title}', can't parse arduboy archive!")
                    if "device" not in binary:
                        raise Exception(f"No device set for binary '{title}', can't parse arduboy archive!")
                    binresult = ArduboyBinary(binary["device"])
                    with open(extract(binary["filename"]),"r") as f: # The arduboy utilities opens with just "r", no binary flags set.
                        binresult.rawhex = f.read()
                    if "flashdata" in binary:
                        with open(extract(binary["flashdata"]), "rb") as f:
                            binresult.data_raw = f.read()
                    if "flashsave" in binary:
                        with open(extract(binary["flashsave"]), "rb") as f:
                            binresult.save_raw = f.read()
                    result.binaries.append(binresult)
            # And now to get data which isn't described in the info.json
            for filename in zip_ref.namelist():
                if filename.lower() != "banner.png" and ((filename.lower().endswith(".png") and not result.image) or filename.lower() == "title.png"):
                    try:
                        extract_file = extract(filename)
                        # NOTE: we don't resize the image, since we don't know what people want to do with it!
                        with Image.open(extract_file) as img:
                            result.image = img.copy() # Image.open(extract_file)  # pilimage_titlescreen(Image.open(extract_file))
                    except Exception as ex:
                        logging.warning(f"Couldn't load title image: {ex} (ignoring)")

        if not result.rawhex:
            raise Exception("No .hex file read from arduboy file!")
    return result

# Write the given parsed arduboy back to the filesystem
def write(ard_parsed: ArduboyParsed, filepath: str):
    logging.debug(f"Writing data to arduboy file: {filepath}")
    with tempfile.TemporaryDirectory() as tempdir:
        files = []
        # First, let's create the object that will be json later. We may modify it!
        info = { 
            "schemaVersion" : 3, 
            "binaries" : [], 
        }
        ard_parsed.fill_info(info)
        # Make SURE there is a title, even though fill_info sets it if it exists!
        info["title"] = ard_parsed.title or ard_parsed.original_filename or Path(filepath).stem 
        # Write the title image
        files.append(os.path.join(tempdir, "title.png"))
        ard_parsed.image.save(files[-1])
        # Next, write all the binaries
        for binary in ard_parsed.binaries:
            bindata = { "device" : binary.device or DEVICE_UNKNOWN }
            bindata["title"] = info["title"] + "_" + bindata["device"]
            def write_bin(data, field, nameappend, mode):
                if data and len(data) > 0:
                    bindata[field] = slugify(bindata["title"]) + nameappend
                    files.append(os.path.join(tempdir, bindata[field]))
                    with open(files[-1], mode) as f:
                        f.write(data)
            write_bin(binary.rawhex, "filename", ".hex", "w")
            write_bin(binary.data_raw, "flashdata", "_data.bin", "wb")
            write_bin(binary.save_raw, "flashsave", "_save.bin", "wb")
        # Finally, write the info.json file
        files.append(os.path.join(tempdir, "info.json"))
        demjson3.encode_to_file(files[-1], info, compactly=False)
        # Zip it all uuuppp!!
        with zipfile.ZipFile(filepath, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for fp in files:
                zipf.write(fp, arcname=os.path.basename(fp))

# Parse pages and data relevant for flashing out of the parsed arduboy file
# Throws an exception if the records can't be validated. Taken almost verbatim from 
# https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/uploader.py
def parse(arduboy_data: ArduboyParsed):
    logging.debug(f"Parsing arduboy data {arduboy_data}")
    result = ArduhexParsed(arduboy_data)
    records = arduboy_data.rawhex.splitlines()
    flash_addr = 0
    # NOTE: this is a simple Intel HEX format: https://en.wikipedia.org/wiki/Intel_HEX
    for rcd in records :
        # Assuming this is some kind of end symbol
        if rcd == ":00000001FF": 
            break
        elif rcd[0] == ":" :
            # This part is literally just copy + paste, the hex format seems complicated...
            rcd_len  = int(rcd[1:3],16)
            rcd_addr = int(rcd[3:7],16)
            rcd_typ  = int(rcd[7:9],16)
            rcd_end = 9 + rcd_len*2
            rcd_sum  = int(rcd[rcd_end:rcd_end+2],16)
            if (rcd_typ == 0) and (rcd_len > 0) :
                flash_addr = rcd_addr
                result.flash_page_used[int(rcd_addr / FLASH_PAGESIZE)] = True
                result.flash_page_used[int((rcd_addr + rcd_len - 1) / FLASH_PAGESIZE)] = True
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

# Convert a raw binary back into hex! 
def unparse(bindata: bytearray, bytes_per_record = BYTES_PER_RECORD) -> str:
    logging.debug(f"UNParsing arduboy binary data ({len(bindata)} bytes) back to hex")
    if bytes_per_record > 255:
        raise Exception("Too many bytes per record! Limit 255")
    hexstring = ""
    # Hex files seem to start at 0, so we can reuse the index as the flash address
    for flash_addr in range(0, len(bindata), bytes_per_record):
        # Pull a limited number of bytes out of the data (based on bytes per record)
        rec_bytes = bindata[flash_addr:flash_addr + bytes_per_record]
        # First part of the line is the number of bytes, address, and record type (always 0)
        line = hex(len(rec_bytes))[2:].zfill(2) + hex(flash_addr)[2:].zfill(4) + "00"
        # Then the chosen number of bytes in hex
        line += binascii.hexlify(rec_bytes).decode()
        # THe checksum portion is the sum of all the bytes on the line other than the checksum itself and the initial symbols (: and etc)
        checksum = sum(bytes.fromhex(line))
        # but then least significant byte + two's compliment. LSB 
        checksum = (~(checksum & 0xFF) + 1) & 0xFF
        hexstring += ":" + (line + hex(checksum)[2:].zfill(2)).upper() + "\n"
    return hexstring + ":00000001FF"
