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

CATEGORY_HEADER_INDEX = 7        # Index into slot header for category (1 byte)
SLOT_SIZE_HEADER_INDEX = 12      # Index into header for slot size. (2 bytes)
PROGRAM_SIZE_HEADER_INDEX = 14   # Index into header for program size (1 byte)

# Each slot has a "string" section of the header which stores up to 4 
# pieces of data. Although categories will only have (title, info), and
# any section may be truncated since only 199 characters are saved.
@dataclass
class FxSlotMeta:
    title: str
    version: str
    developer: str
    info: str

@dataclass
class FxParsedSlot:
    category: int
    image: Image
    program_hex: str
    data_raw: bytearray
    save_raw: bytearray
    meta: FxSlotMeta

    # For now, category calculation is simple: when there's no program
    def is_category(self):
        return len(self.program_hex) == 0

    # def progdata_hash(self):
    #     sha256(self.p self.data_raw)

# Read and pad the fx data from the given file and return the bytearray
def read(filename):
    logging.debug(f'Reading flash image from file "{filename}"')
    with open(filename, "rb") as f:
        flashdata = bytearray(f.read())
    return arduboy.utils.pad_data(flashdata, FX_PAGESIZE)


def default_header():
    return bytearray(HEADER_START_STRING.encode() + (b'\xFF' * (HEADER_LENGTH - len(HEADER_START_STRING))))

# Get whether the data in the given position is an FX slot
def is_slot(fulldata, index):
    return HEADER_START_BYTES == fulldata[index:index+len(HEADER_START_BYTES)]

# Get the size IN BYTES of the fx slot! The index should be the start of the slot!
def get_slot_size_bytes(fulldata, index):
    # Get 2 consecutive bytes and return as 1 value (big endian)
    return struct.unpack(">H", fulldata[index + SLOT_SIZE_HEADER_INDEX : index + SLOT_SIZE_HEADER_INDEX + 2])[0] * FX_PAGESIZE 

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
    # Data apparently goes right to the end of the slot!
    return fulldata[index + HEADER_LENGTH + TITLE_IMAGE_LENGTH + get_program_size_bytes(fulldata, index) : get_slot_size_bytes(fulldata, index)]


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
        # TODO: get save data if it exists! Also, get the hash and extra data!

        result.append(FxParsedSlot(
            category_raw, 
            arduboy.utils.bin_to_pilimage(image_raw), 
            arduboy.utils.bin_to_hexrecords(program_raw), 
            datapart_raw
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
