# NOTE: a lot of this code is adapted (with heavy modifications) from
# https://github.com/MrBlinky/Arduboy-Python-Utilities

from hashlib import sha256
import logging
import arduboy.device
import arduboy.utils
import struct
# import sqlite3

from arduboy.constants import *
from dataclasses import dataclass, field
from PIL import Image


HEADER_START_STRING = "ARDUBOY"
HEADER_START_BYTES = bytearray(HEADER_START_STRING.encode())

HEADER_LENGTH = 256          # The flashcart slot header length in bytes
TITLE_IMAGE_LENGTH = 1024    # The flashcart slot title image length in bytes
HEADER_PROGRAM_FACTOR = 128  # Multiply the flashcart slot program length by this

CATEGORY_HEADER_INDEX = 7           # "Index into slot header for" category (1 byte)
PREVIOUS_PAGE_HEADER_INDEX = 8      # "" previous slot page (2 bytes)
NEXT_PAGE_HEADER_INDEX = 10         # "" next slot page (2 bytes)
SLOT_SIZE_HEADER_INDEX = 12         # "" slot size. (2 bytes)
PROGRAM_SIZE_HEADER_INDEX = 14      # "" program size (1 byte)
DATAPAGE_HEADER_INDEX = 17          # "" starting page of data (2 bytes)
SAVEPAGE_HEADER_INDEX = 19          # "" starting page of save (2 bytes)

# Each slot has a "string" section of the header which stores up to 4 
# pieces of data. Although categories will only have (title, info), and
# any section may be truncated since only 199 characters are saved.
@dataclass
class FxSlotMeta:
    title: str
    version: str
    developer: str
    info: str

# Note: Although it says "parsed", I just mean it was parsed out of the giant binary blob.
# The individual fields are not parsed, in case you want to immediately turn around and rewrite
# it to the cart (which is likelY), plus I don't know how you might want to use all the data.
@dataclass
class FxParsedSlot:
    category: int
    image_raw: bytearray
    program_raw: bytearray
    data_raw: bytearray
    save_raw: bytearray
    meta: FxSlotMeta

    # For now, category calculation is simple: when there's no program
    def is_category(self):
        return len(self.program_raw) == 0

    # def progdata_hash(self):
    #     sha256(self.p self.data_raw)

# Read and pad the fx data from the given file and return the bytearray
def read(filename):
    logging.debug(f'Reading flash image from file "{filename}"')
    with open(filename, "rb") as f:
        flashdata = bytearray(f.read())
    return arduboy.utils.pad_data(flashdata, FX_PAGESIZE)

# ----------------------
#    HEADER PARSING
# ----------------------

def default_header():
    return bytearray(HEADER_START_STRING.encode() + (b'\xFF' * (HEADER_LENGTH - len(HEADER_START_STRING))))

# Get whether the data in the given position is an FX slot
def is_slot(fulldata, index):
    return HEADER_START_BYTES == fulldata[index:index+len(HEADER_START_BYTES)]

# Get 2 consecutive bytes and return as 1 value (big endian). Several header values use this
def get_2byte_value(fulldata, index):
    return struct.unpack(">H", fulldata[index: index + 2])[0]

# Get the size IN BYTES of the fx slot! The index should be the start of the slot!
def get_slot_size_bytes(fulldata, index):
    return get_2byte_value(fulldata, index + SLOT_SIZE_HEADER_INDEX) * FX_PAGESIZE

def get_data_page(fulldata, index):
    return get_2byte_value(fulldata, index + DATAPAGE_HEADER_INDEX)

def get_save_page(fulldata, index):
    return get_2byte_value(fulldata, index + SAVEPAGE_HEADER_INDEX)

# Get the size in bytes of the program data! The index should be the start of the slot! May not be the exact size!
def get_program_size_bytes(fulldata, index):
    return fulldata[index + PROGRAM_SIZE_HEADER_INDEX] * HEADER_PROGRAM_FACTOR

# Get the category of this slot. As usual, index should be the start of the slot
def get_category(fulldata, index):
    # Just a single byte for category!
    return fulldata[index + CATEGORY_HEADER_INDEX]

# Get the title image BYTES of this slot. As usual, index should be the start of the slot
def get_title_image_raw(fulldata, index):
    return fulldata[index + HEADER_LENGTH : index + HEADER_LENGTH + TITLE_IMAGE_LENGTH]

# Get the program BYTES of this slot. As usual, index should be the start of the slot. Might be an empty array!
def get_program_raw(fulldata, index):
    progstart = index + HEADER_LENGTH + TITLE_IMAGE_LENGTH
    return fulldata[progstart : progstart + get_program_size_bytes(fulldata, index)]

# Get the "extra data" which might be packed with a sketch (for FX-enabled programs!)
def get_datapart_raw(fulldata, index):
    # Skip data reading if no data page set
    dpage = get_data_page(fulldata, index)
    if dpage == 0xFFFF:
        return []
    dindex = dpage * FX_PAGESIZE # index + HEADER_LENGTH + TITLE_IMAGE_LENGTH + get_program_size_bytes(fulldata, index)
    # There are two options: if there's no save data, the data goes right to the end. Otherwise, 
    # we have to do something funny
    spage = get_save_page(fulldata, index)
    if spage == 0xFFFF:
        return fulldata[dindex:get_slot_size_bytes(fulldata, index)]
    else:
        save_start = spage * FX_PAGESIZE
        data = fulldata[dindex:save_start]
        # Now for a funny part: we scan the chunks of 256 bytes at the end, and while they are all 0xFF,
        # we remove them. This is because, if there is a save, it is aligned to 4k blocks (flash is written
        # in 4k portions), but the data size is not stored, so there may be lots of padding between the data
        # and save data portions. We only need to do this if there is save data
        last_FF_index = 0 # Loop will exit without assignment if ALL are 0xFF
        for i in range(len(data) - 1, -1, -1):
            if data[i] != 0xFF:
                last_FF_index = i + 1 # If the very last byte isn't FF, index will be outside range, math still works
                break
        unused_pages = (len(data) - last_FF_index) // FX_PAGESIZE
        return data[:len(data) - FX_PAGESIZE * unused_pages]

# Get the save data which might be packed with a sketch (for FX-enabled programs!)
def get_savepart_raw(fulldata, index):
    spage = get_save_page(fulldata, index)
    if spage == 0xFFFF:
        return []
    else:
        return fulldata[spage*FX_PAGESIZE:get_slot_size_bytes(fulldata, index)]


# Trim the given fx cart data
def trim(fullBinaryData):
    # There is a 2 byte section of each FX slot header which tells the PAGE size of the entire slot. We use that to jump
    # through all the slots without parsing
    currentHeaderIndex = 0
    while currentHeaderIndex < len(fullBinaryData)-1:
        if not is_slot(fullBinaryData, currentHeaderIndex):
            break
        currentHeaderIndex += get_slot_size_bytes(fullBinaryData, currentHeaderIndex)
    logging.debug(f"Trim fx cart from {len(fullBinaryData)} -> {currentHeaderIndex} bytes")
    return fullBinaryData[0:currentHeaderIndex]

# Trim the given fx cart file and output to another file. NOTE: they can be the same file
def trim_file(infile, outfile = None):
    if not outfile:
        outfile = infile
        logging.debug(f"Trimming binary file {infile} (in-place)")
    else:
        logging.debug(f"Scanning binary file {infile} and storing trimmed output to {outfile}")
    
    with open(infile, 'rb') as ifile:
        binaryData = ifile.read()

    trimmedBinData = trim(binaryData)

    with open(outfile, 'wb') as ofile:
        ofile.write(trimmedBinData)


# Given an entire FX binary, parse absolutely everything out of it (in slot format)
def parse(fulldata, report_progress):

    logging.debug(f"Full parsing FX cart ({len(fulldata)} bytes)")
    dindex = 0
    result = []

    while dindex < len(fulldata)-1:
        if not is_slot(fulldata, dindex):
            break

        slotsize = get_slot_size_bytes(fulldata, dindex)
        category_raw = get_category(fulldata, dindex)
        image_raw = get_title_image_raw(fulldata, dindex)
        program_raw = get_program_raw(fulldata, dindex)
        datapart_raw = get_datapart_raw(fulldata, dindex)
        savepart_raw = get_datapart_raw(fulldata, dindex)
        # TODO: get save data if it exists! Also, get the hash and extra data!

        result.append(FxParsedSlot(
            category_raw, 
            image_raw,
            #arduboy.utils.bin_to_pilimage(image_raw), 
            program_raw, # What about parsing the bin? UGH! Most of the time we want the raw, not the parsed, someone else can do that
            #arduboy.utils.bin_to_hexrecords(program_raw), 
            datapart_raw,
            savepart_raw
        ))

        dindex += slotsize

        report_progress(dindex, len(fulldata))

    logging.info(f"Fully parsed {(len(result))} program sections")

    return result


# Compile the given parsed data of an arduboy cart back into bytes
def compile(parsed_records, report_progress):
    pass

# # Create a database to store programs
# def make_database(filepath):
#     with sqlite3.connect(filepath) as con:
#         cursor = con.cursor()
#         cursor.execute("""
#             CREATE TABLE IF NOT EXISTS categories(
#                 
#             )
#                       """)
# 
