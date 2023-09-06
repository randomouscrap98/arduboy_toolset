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
import slugify

from intelhex import IntelHex
from io import BytesIO, StringIO
from pathlib import Path
from typing import List
from dataclasses import dataclass, field, asdict
from PIL import Image

"""Number of default bytes per record when writing a .hex file"""
BYTES_PER_RECORD = 16
CATERINA_PAGE = 224
DEFAULT_SCHEMA = 4  # Schema version for .arduboy package info.json

DEFAULT_CARTIMAGE = "cart.png"
INFO_FILE = "info.json"

DEVICE_ARDUBOY = "Arduboy"
DEVICE_ARDUBOYFX = "ArduboyFX"
DEVICE_ARDUBOYMINI = "ArduboyMini"

DEVICE_DEFAULT = DEVICE_ARDUBOY
ALLOWED_DEVICES = [ DEVICE_ARDUBOY, DEVICE_ARDUBOYFX, DEVICE_ARDUBOYMINI ]


@dataclass
class ArduboyBinary:
    """A single "binary" field from a .arduboy file"""
    device: str = field(default="")
    hex_raw: str = field(default="")
    data_raw: bytearray = field(default_factory=lambda:bytearray())
    save_raw: bytearray = field(default_factory=lambda:bytearray())
    cartImage: Image = field(default=None)

@dataclass
class ArduboyContributor:
    """One contributor on a project. Most fields are optional, other than the name"""
    name: str = field()
    contributions: List[str] = field(default_factory=lambda: [])
    urls: List[str] = field(default_factory=lambda: [])

@dataclass
class ArduboyParsed:
    """Represents as much data as possible pulled from either a .arduboy file or a .hex sketch.
    
    Only fields which were found will be set; all fields have reasonable defaults.
    """
    original_filename: str

    binaries: List[ArduboyBinary] = field(default_factory=lambda: [])
    contributors: List[ArduboyContributor] = field(default_factory=lambda: [])

    # Some of the more "required" fields
    title: str = field(default="")
    version: str = field(default="")
    author: str = field(default="")
    description: str = field(default="")

    # Some optional fields
    date : str = field(default=None)
    genre : str = field(default=None)
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
        for f in ["title", "author", "description", "version", "genre", "date", "url", "sourceUrl", "email", "companion"]:
            func(info, f)
    
    def fill_with_info(self, info):
        """Fill self with the info given. In other words, convert info json into a ArduboyParsed"""
        ArduboyParsed._fill_generic(info, self._set_self)

    def fill_info(self, info):
        """Fill info with data from self. In other words, convert ArduboyParsed into info json"""
        ArduboyParsed._fill_generic(info, self._set_info)
    
    def _set_self(self, info, field):
        if field in info:
            setattr(self, field, info[field])
        return getattr(self, field)
    
    def _set_info(self, info, field):
        value = getattr(self, field)
        if value is not None:
            info[field] = value
        return value


def read_any(filepath: str) -> ArduboyParsed:
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

def read_hex(filepath: str, device: str = DEVICE_DEFAULT) -> ArduboyParsed:
    """Read a single hex file as a full ArduboyParsed object. Most fields will be unset"""
    logging.debug(f"Reading data from hex file: {filepath}")
    result = ArduboyParsed(Path(filepath).stem)
    with open(filepath,"r") as f:
        binary = ArduboyBinary(device = device, hex_raw = f.read())
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
            def extract_image(fn): # Simple function to get a parsed PIL.Image from the zip
                extract_file = extract(fn)
                with Image.open(extract_file) as img:
                    return img.copy() # This seems stupid, sorry
            extract_file = extract(INFO_FILE)
            info = demjson3.decode_file(extract_file, encoding="utf-8", strict=False)
            result.fill_with_info(info) # Fills in all the boring easy fields
            try:
                default_cartimage = extract_image(DEFAULT_CARTIMAGE)
            except Exception as ex:
                logging.debug("No default cart image found")
                default_cartimage = None
            sversion = info["schemaVersion"] if "schemaVersion" in info else None
            if sversion == 3:
                key_program = "filename"
                key_data = "flashdata"
                key_save = "flashsave"
            else:
                key_program = "program"
                key_data = "flashData"
                key_save = "flashSave"
            if "contributors" in info:
                for contributor in info["contributors"]:
                    rescon = ArduboyContributor(contributor["name"] if "name" in contributor else "UNKNOWN")
                    if "contributions" in contributor:
                        rescon.contributions = list(contributor["contributions"])
                    if "urls" in contributor:
                        rescon.urls = list(contributor["urls"])
                    result.contributors.append(rescon)
            # Now we must go manually extract some files! Binaries are a complicated business!
            if "binaries" in info:
                for binary in [x for x in info["binaries"] if "title" in x]:
                    title = binary["title"]
                    if key_program not in binary:
                        raise Exception(f"No {key_program} set for binary '{title}', can't parse arduboy archive!")
                    if "device" not in binary:
                        raise Exception(f"No device set for binary '{title}', can't parse arduboy archive!")
                    binresult = ArduboyBinary(binary["device"])
                    with open(extract(binary[key_program]),"r") as f: # The arduboy utilities opens with just "r", no binary flags set.
                        binresult.hex_raw = f.read()
                    if key_data in binary:
                        with open(extract(binary[key_data]), "rb") as f:
                            binresult.data_raw = f.read()
                    if key_save in binary:
                        with open(extract(binary[key_save]), "rb") as f:
                            binresult.save_raw = f.read()
                    if "cartImage" in binary:
                        binresult.cartImage = extract_image(binary["cartImage"])
                    elif default_cartimage:
                        binresult.cartImage = default_cartimage.copy()
                    result.binaries.append(binresult)
            if len(result.binaries) == 0:
                raise Exception(f"No usable binaries found in arduboy file {filepath}")
    return result


def write_arduboy(ard_parsed: ArduboyParsed, filepath: str):
    """Write the given parsed arduboy data back to the filesystem. 
    
    Note that no checks are performed; you may write back an unusable arduboy package.
    """
    logging.debug(f"Writing data to arduboy file: {filepath}")
    with tempfile.TemporaryDirectory() as tempdir:
        files = []
        # First, let's create the object that will be json later. We may modify it!
        info = { 
            "schemaVersion" : DEFAULT_SCHEMA, 
            "binaries" : [], 
            "contributors" : [ asdict(x) for x in ard_parsed.contributors ] # Just a mostly direct use, very simple
        }
        ard_parsed.fill_info(info) # All the easy info we don't have to worry about
        # Make SURE there is a title, even though fill_info sets it if it exists!
        info["title"] = ard_parsed.title or ard_parsed.original_filename or Path(filepath).stem 
        # Next, write all the binaries
        for binary in ard_parsed.binaries:
            bindata = { "device" : binary.device or DEVICE_DEFAULT }
            bindata["title"] = info["title"] + " - " + bindata["device"]
            def set_file_field(field, nameappend):
                bindata[field] = slugify.slugify(bindata["title"]) + nameappend
                files.append(os.path.join(tempdir, bindata[field]))
                return files[-1]
            def write_bin(data, field, nameappend, mode):
                if data and len(data) > 0:
                    filename = set_file_field(field, nameappend)
                    with open(filename, mode) as f:
                        f.write(data)
            write_bin(binary.hex_raw, "program", ".hex", "w")
            write_bin(binary.data_raw, "flashData", "_data.bin", "wb")
            write_bin(binary.save_raw, "flashSave", "_save.bin", "wb")
            # Write the title image
            if binary.cartImage:
                filename = set_file_field("cartImage", "_cartimage.png")
                binary.cartImage.save(filename)
            info["binaries"].append(bindata)
        # Finally, write the info.json file
        files.append(os.path.join(tempdir, "info.json"))
        demjson3.encode_to_file(files[-1], info, compactly=False)
        # Zip it all uuuppp!!
        with zipfile.ZipFile(filepath, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for fp in files:
                zipf.write(fp, arcname=os.path.basename(fp))


def hex_to_bin(rawhex: str) -> bytearray:
    """Convert raw hex string (intel hex format) to raw bytearray
    
    Returns:
        Full sketch binary (with padding, so 32kb)
    """
    buffer = StringIO(rawhex)
    ihex = IntelHex(buffer)
    return bytearray(ihex.tobinarray(start=0, size=FLASH_SIZE))

def bin_to_hex(rawbin: bytearray, recordsize: int = 16) -> str:
    """Convert raw bytearray to intel hex string.
    
    Returns:
        A string representing the hex file, completely unchanged
    """
    buffer = BytesIO(rawbin)
    ihex = IntelHex()
    ihex.loadbin(buffer)
    outbuffer = StringIO()
    ihex.write_hex_file(outbuffer, byte_count=recordsize)
    return outbuffer.getvalue()


@dataclass
class SketchAnalysis:
    overwrites_caterina: bool = field(default=False)
    total_pages: int = field(default=0)
    used_pages: List[bool] = field(default_factory=lambda: [False] * FLASH_PAGECOUNT)
    trimmed_data: bytearray = field(default_factory=lambda: bytearray())

def analyze_sketch(bindata: bytearray) -> SketchAnalysis:
    """Analyze a sketch binary for various information.
    
    Returns:
        A SketchAnalysis object with information such as the used pages, total pages, and a 
        copy of the data but trimmed to a page-aligned minimum size. If no trimming was performed,
        the trimmed size is the exact size of the input, without any page alignment
    """
    result = SketchAnalysis()
    # Some of this is guesswork but it should be good enough I think...
    lastpage = FLASH_PAGECOUNT
    for page in range(FLASH_PAGECOUNT):
        start = page * FLASH_PAGESIZE
        if len(bindata) > start and sum(bindata[page * FLASH_PAGESIZE : (page + 1) * FLASH_PAGESIZE]) != 0xFF * FLASH_PAGESIZE:
            result.used_pages[page] = True
            result.total_pages += 1
            lastpage = page
            if page >= CATERINA_PAGE:
                result.overwrites_caterina = True
    result.trimmed_data = bindata[:(lastpage + 1) * FLASH_PAGESIZE]
    return result

