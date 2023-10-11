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

from pathlib import Path
from typing import List
from dataclasses import dataclass, field, asdict
from PIL import Image


CATERINA_PAGE = 224     # Number of default bytes per record when writing a .hex file
DEFAULT_SCHEMA = 4      # Schema version for .arduboy package info.json

DEFAULT_CARTIMAGE = "cart.png"
INFO_FILE = "info.json"
LICENSE_FILE = "LICENSE.txt"

LICENSE_FILES = [ LICENSE_FILE, "LICENCE.txt", "LICENSE", "LICENCE" ]

KEY_SCHEMA = "schemaVersion"
KEY_BINFILE = "filename"
KEY_DATAFILE = "flashdata"
KEY_SAVEFILE = "flashsave"
KEY_CARTIMAGE = "cartimage"
KEY_CONTRIB_ROLES = "roles"
KEY_CONTRIB_URLS = "urls"
KEY_CONTRIBUTORS = "contributors"
KEY_DEVICE = "device"
KEY_TITLE = "title"
KEY_BINARIES = "binaries"

OLD_CONTRIBUTOR_KEYS = ["publisher", "idea", "code", "art", "sound"]

ARDUBOYFX_ENABLE_BYTES = bytes.fromhex("5998")
ARDUBOYFX_DISABLE_BYTES = bytes.fromhex("599a")
ARDUBOYMINI_ENABLE_BYTES = bytes.fromhex("7298")    # 0x72, 0x98, 0x0e, 0x94
ARDUBOYMINI_DISABLE_BYTES = bytes.fromhex("729a")   # 0x72, 0x9a, 0x08, 0x95

ARDUBOY_RET_BYTES = bytes.fromhex("0895") # 0x59, 0x9a, 0x08, 0x95
ARDUBOY_CALL_BYTES = bytes.fromhex("0e94") # 0x59, 0x9a, 0x08, 0x95

def find_call_ret(bindata, initial):
    ret = initial + ARDUBOY_RET_BYTES
    call = initial + ARDUBOY_CALL_BYTES
    return bindata.find(ret) >= 0 or bindata.find(call) >= 0
    # pos = bindata.find(initial)
    # if pos >= 0:
    #     return bindata.find(ARDUBOY_RET_BYTES, pos + 1) == pos + 1 or bindata.find(ARDUBOY_)
    # else :
    #     return False
    # return bindata.find(initial) and (bindata.)

 ## ARDUBOYFX_ENABLE_BYTES = bytes.fromhex("59980e94") # bytearray(0x59, 0x98, 0x0e, 0x94)
 #ARDUBOYFX_DISABLE_1 = bytes.fromhex("599a0895") # 0x59, 0x9a, 0x08, 0x95
 #ARDUBOYFX_DISABLE_2 = bytes.fromhex("599a0e94") # 0x59, 0x9a, 0x0e, 0x94
 #ARDUBOYMINI_ENABLE_BYTES = bytes.fromhex("72980e94") # 0x72, 0x98, 0x0e, 0x94
 #ARDUBOYMINI_DISABLE_1 = bytes.fromhex("729a0895") # 0x72, 0x9a, 0x08, 0x95
 #ARDUBOYMINI_DISABLE_2 = bytes.fromhex("729a0e94") # 0x72, 0x9a, 0x0e, 0x94

DEVICE_ARDUBOY = "Arduboy"
DEVICE_ARDUBOYFX = "ArduboyFX"
DEVICE_ARDUBOYMINI = "ArduboyMini"

DEVICE_DEFAULT = DEVICE_ARDUBOY
ALLOWED_DEVICES = [ DEVICE_ARDUBOY, DEVICE_ARDUBOYFX, DEVICE_ARDUBOYMINI ]

def device_allowed(real_device: str, test_device: str) -> bool:
    """Determine whether the given actual device is allowed to use binaries from the given test device"""
    return test_device.lower() == DEVICE_ARDUBOY.lower() or real_device.lower() == test_device.lower()


@dataclass
class ArduboyBinary:
    """A single "binary" field from a .arduboy file"""
    device: str = field(default="")
    title: str = field(default="")
    hex_raw: str = field(default="")
    data_raw: bytearray = field(default_factory=lambda:bytearray())
    save_raw: bytearray = field(default_factory=lambda:bytearray())
    cartImage: Image = field(default=None)

    def fx_enabled(self):
        return (self.data_raw and len(self.data_raw) > 0) or (self.save_raw and len(self.save_raw) > 0)

@dataclass
class ArduboyContributor:
    """One contributor on a project. Most fields are optional, other than the name"""
    name: str = field()
    roles: List[str] = field(default_factory=lambda: [])
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

    license: str = field(default=None)

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
        
        In other words, these are all the fields that are shared between the two formats. They're all
        basic strings 
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


def empty_parsed_arduboy() -> ArduboyParsed:
    """A fully empty arduboy data object. Is this useful?"""
    return ArduboyParsed(None)


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
        binary = ArduboyBinary(device = device, hex_raw = f.read(), title = result.original_filename)
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
            for lf in LICENSE_FILES:
                try:
                    license_file = extract(lf)
                    with open(license_file, "r", encoding="utf-8") as f:
                        result.license = f.read()
                    break
                except:
                    logging.debug(f"No license in '{lf}'")
            if not result.license:
                logging.warning("No license file found!")
            if KEY_CONTRIBUTORS in info:
                for contributor in info[KEY_CONTRIBUTORS]:
                    rescon = ArduboyContributor(contributor["name"] if "name" in contributor else "UNKNOWN")
                    if KEY_CONTRIB_ROLES in contributor:
                        rescon.roles = list(contributor[KEY_CONTRIB_ROLES])
                    if KEY_CONTRIB_URLS in contributor:
                        rescon.urls = list(contributor[KEY_CONTRIB_URLS])
                    result.contributors.append(rescon)
            # Convert old contributor fields to the new format
            for f in OLD_CONTRIBUTOR_KEYS:
                if f in info:
                    user = info[f]
                    if not user:
                        continue
                    contribution = f.capitalize()
                    found = False
                    for c in result.contributors:
                        if c.name == user:
                            c.roles.append(contribution)
                            found = True
                            break
                    if not found:
                        result.contributors.append(ArduboyContributor(user, [contribution]))
            # Now we must go manually extract some files! Binaries are a complicated business!
            if KEY_BINARIES in info:
                for binary in [x for x in info[KEY_BINARIES] if KEY_TITLE in x]:
                    title = binary[KEY_TITLE]
                    if KEY_BINFILE not in binary:
                        raise Exception(f"No {KEY_BINFILE} set for binary '{title}', can't parse arduboy archive!")
                    if KEY_DEVICE not in binary:
                        raise Exception(f"No device set for binary '{title}', can't parse arduboy archive!")
                    binresult = ArduboyBinary(binary[KEY_DEVICE], title)
                    with open(extract(binary[KEY_BINFILE]),"r") as f: # The arduboy utilities opens with just "r", no binary flags set.
                        binresult.hex_raw = f.read()
                    if KEY_DATAFILE in binary:
                        with open(extract(binary[KEY_DATAFILE]), "rb") as f:
                            binresult.data_raw = f.read()
                    if KEY_SAVEFILE in binary:
                        with open(extract(binary[KEY_SAVEFILE]), "rb") as f:
                            binresult.save_raw = f.read()
                    if KEY_CARTIMAGE in binary:
                        binresult.cartImage = extract_image(binary[KEY_CARTIMAGE])
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
            KEY_SCHEMA : DEFAULT_SCHEMA, 
            KEY_BINARIES : [], 
            KEY_CONTRIBUTORS : [ asdict(x) for x in ard_parsed.contributors ] # Just a mostly direct use, very simple
        }
        ard_parsed.fill_info(info) # All the easy info we don't have to worry about
        # Make SURE there is a title, even though fill_info sets it if it exists!
        info[KEY_TITLE] = ard_parsed.title or ard_parsed.original_filename or Path(filepath).stem 
        # Next, write all the binaries
        for binary in ard_parsed.binaries:
            bindata = { KEY_DEVICE : binary.device or DEVICE_DEFAULT }
            bindata[KEY_TITLE] = binary.title or (info[KEY_TITLE] + " - " + bindata[KEY_DEVICE])
            def set_file_field(field, nameappend):
                bindata[field] = slugify.slugify(bindata[KEY_TITLE]) + nameappend
                files.append(os.path.join(tempdir, bindata[field]))
                return files[-1]
            def write_bin(data, field, nameappend, mode):
                if data and len(data) > 0:
                    filename = set_file_field(field, nameappend)
                    with open(filename, mode) as f:
                        f.write(data)
            write_bin(binary.hex_raw, KEY_BINFILE, ".hex", "w")
            write_bin(binary.data_raw, KEY_DATAFILE, "_data.bin", "wb")
            write_bin(binary.save_raw, KEY_SAVEFILE, "_save.bin", "wb")
            # Write the title image
            if binary.cartImage:
                filename = set_file_field(KEY_CARTIMAGE, "_cartimage.png")
                binary.cartImage.save(filename)
            info[KEY_BINARIES].append(bindata)
        # Write the license file (if it exists)
        if ard_parsed.license:
            files.append(os.path.join(tempdir, LICENSE_FILE))
            with open(files[-1], "w", encoding="utf-8") as f:
                f.write(ard_parsed.license)
        # Finally, write the info.json file
        files.append(os.path.join(tempdir, INFO_FILE))
        demjson3.encode_to_file(files[-1], info, compactly=False)
        # Zip it all uuuppp!!
        with zipfile.ZipFile(filepath, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
            for fp in files:
                zipf.write(fp, arcname=os.path.basename(fp))


@dataclass
class SketchAnalysis:
    overwrites_caterina: bool = field(default=False)
    total_pages: int = field(default=0)
    used_pages: List[bool] = field(default_factory=lambda: [False] * FLASH_PAGECOUNT)
    trimmed_data: bytearray = field(default_factory=lambda: bytearray())
    detected_device: str = field(default=None)

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
    if find_call_ret(bindata, ARDUBOYFX_ENABLE_BYTES) and find_call_ret(bindata, ARDUBOYFX_DISABLE_BYTES): # bindata.find(ARDUBOYFX_DISABLE_1) >= 0 or bindata.find(ARDUBOYFX_DISABLE_2) >= 0:
    # if bindata.find(ARDUBOYFX_ENABLE_BYTES) >= 0: # and (bindata.find(ARDUBOYFX_DISABLE_1) >= 0 or bindata.find(ARDUBOYFX_DISABLE_2) >= 0):
        result.detected_device = DEVICE_ARDUBOYFX
    # elif bindata.find(ARDUBOYMINI_DISABLE_1) >= 0 or bindata.find(ARDUBOYMINI_DISABLE_2) >= 0:
    elif find_call_ret(bindata, ARDUBOYMINI_ENABLE_BYTES) and find_call_ret(bindata, ARDUBOYMINI_DISABLE_BYTES): # bindata.find(ARDUBOYFX_DISABLE_1) >= 0 or bindata.find(ARDUBOYFX_DISABLE_2) >= 0:
    # elif bindata.find(ARDUBOYMINI_ENABLE_BYTES) >= 0: # and (bindata.find(ARDUBOYMINI_DISABLE_1) >= 0 or bindata.find(ARDUBOYMINI_DISABLE_2) >= 0):
        result.detected_device = DEVICE_ARDUBOYMINI
    else:
        # Probably dangerous to assume it's Arduboy but whatever...
        result.detected_device = DEVICE_ARDUBOY
    return result

