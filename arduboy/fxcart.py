# NOTE: a lot of this code is adapted (with heavy modifications) from
# https://github.com/MrBlinky/Arduboy-Python-Utilities

from arduboy.common import *
from arduboy.constants import *
from arduboy.patch import *

import logging
import struct

from hashlib import sha256
from typing import List
from dataclasses import dataclass, field


HEADER_START_STRING = "ARDUBOY"
HEADER_START_BYTES = bytearray(HEADER_START_STRING.encode())

HEADER_LENGTH = 256          # The flashcart slot header length in bytes
TITLE_IMAGE_LENGTH = 1024    # The flashcart slot title image length in bytes
PREAMBLE_PAGES = (HEADER_LENGTH + TITLE_IMAGE_LENGTH) >> 8 # Page size of entire preamble (includes title)
HEADER_PROGRAM_FACTOR = 128  # Multiply the flashcart slot program length by this
SAVE_ALIGNMENT = 4096

MAX_PROGRAM_LENGTH = HEADER_PROGRAM_FACTOR * 0xFFFF
PROGRAM_NULLPAGE = b'\xFF' * HEADER_PROGRAM_FACTOR

CATEGORY_HEADER_INDEX = 7           # "Index into slot header for" category (1 byte)
PREVIOUS_PAGE_HEADER_INDEX = 8      # "" previous slot page (2 bytes)
NEXT_PAGE_HEADER_INDEX = 10         # "" next slot page (2 bytes)
SLOT_SIZE_HEADER_INDEX = 12         # "" slot size. (2 bytes)
PROGRAM_SIZE_HEADER_INDEX = 14      # "" program size (1 byte, factor of 128)
PROGRAMPAGE_HEADER_INDEX = 15       # "" starting page of program (2 bytes)
DATAPAGE_HEADER_INDEX = 17          # "" starting page of data (2 bytes)
SAVEPAGE_HEADER_INDEX = 19          # "" starting page of save (2 bytes)
DATA_SIZE_HEADER_INDEX = 21         # "" data segment size (2 bytes, factor of 256)
META_HEADER_INDEX = 57              # "" metadata

META_HEADER_SIZE = 199              # Length of the metadata section


@dataclass
class FxSlotMeta:
    """
    Data stored in "string" section of fx slot (last 199 bytes).

    Categories only have title and info. Data is truncated unceremoniously if too long,
    and may even truncate to fewer than 4 total fields if necessary
    """
    title: str
    version: str
    developer: str
    info: str

@dataclass
class FxParsedSlot:
    """
    All data stored in a flashcart "slot", representing one single game.

    Note: Although it says "parsed", I just mean it was parsed out of the giant binary blob.
    The individual fields are not parsed, in case you want to immediately turn around and rewrite
    it to the cart (which is likelY), plus I don't know how you might want to use all the data.
    """
    category: int
    image_raw: bytearray
    program_raw: bytearray
    data_raw: bytearray
    save_raw: bytearray
    meta: FxSlotMeta

    # For now, category calculation is simple: when there's no program
    def is_category(self):
        return len(self.program_raw) == 0
    
    def has_image(self):
        return self.image_raw and sum(self.image_raw) > 0
    
    def fx_enabled(self):
        return (self.data_raw and len(self.data_raw) > 0) or (self.save_raw and len(self.save_raw) > 0)

def empty_slot() -> FxParsedSlot:
    """A fully empty slot, should still be usable in a cart builder or such though."""
    return FxParsedSlot(
        0, bytearray(SCREEN_BYTES), bytearray(), bytearray(), bytearray(), FxSlotMeta("", "", "", "")
    )


# Read and pad the fx flash image from the given file and return the bytearray
def read(filename: str) -> bytearray:
    logging.debug(f'Reading flash image from file "{filename}"')
    with open(filename, "rb") as f:
        flashdata = bytearray(f.read())
    return pad_data(flashdata, FX_PAGESIZE)

# Read and pad the fx data (individual) from the given file and return the byte array.
def read_data(filename: str) -> bytearray:
    logging.debug(f'Reading fx data from file "{filename}"')
    with open(filename, "rb") as f:
        flashdata = bytearray(f.read())
    return pad_data(flashdata, FX_PAGESIZE)


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

# Write the given value into the given array starting at the given index. Should be readable
# by get_2byte_value (big endian)
def write_2byte_value(value, fulldata, index):
    fulldata[index] = value >> 8
    fulldata[index + 1] = value & 0xFF

# Get the size IN BYTES of the fx slot! The index should be the start of the slot!
def get_slot_size_bytes(fulldata, index):
    return get_2byte_value(fulldata, index + SLOT_SIZE_HEADER_INDEX) * FX_PAGESIZE

def get_program_page(fulldata, index):
    return get_2byte_value(fulldata, index + PROGRAMPAGE_HEADER_INDEX)

def get_data_page(fulldata, index):
    return get_2byte_value(fulldata, index + DATAPAGE_HEADER_INDEX)

def get_save_page(fulldata, index):
    return get_2byte_value(fulldata, index + SAVEPAGE_HEADER_INDEX)

# Get the size in bytes of the program data! The index should be the start of the slot! May not be the exact size!
def get_program_size_bytes(fulldata, index):
    return fulldata[index + PROGRAM_SIZE_HEADER_INDEX] * HEADER_PROGRAM_FACTOR

# Get the size in pages of the data section. We do pages instead of bytes because this
# field may not actually be set properly!
def get_data_size_pages(fulldata, index):
    return get_2byte_value(fulldata, index + DATA_SIZE_HEADER_INDEX)

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
        return bytearray()
    dindex = dpage * FX_PAGESIZE # index + HEADER_LENGTH + TITLE_IMAGE_LENGTH + get_program_size_bytes(fulldata, index)
    # There are THREE options: if the data size is set, we're good to go, nothing else to do. Otherwise, 
    # if there's no save data, the data goes right to the end. If all else fails, we have to do something funny
    dpages = get_data_size_pages(fulldata, index)
    spage = get_save_page(fulldata, index)
    if dpages != 0xFFFF:
        return fulldata[dindex:dindex+dpages*FX_PAGESIZE]
    elif spage == 0xFFFF:
        ssize = get_slot_size_bytes(fulldata, index)
        return fulldata[dindex:index+ssize]
    else:
        save_start = spage * FX_PAGESIZE
        data = fulldata[dindex:save_start]
        # Now for a funny part: we scan the chunks of 256 bytes at the end, and while they are all 0xFF,
        # we remove them. This is because, if there is a save, it is aligned to 4k blocks (flash is written
        # in 4k portions), but the data size is not stored, so there may be lots of padding between the data
        # and save data portions. We only need to do this if there is save data
        unused_pages = count_unused_pages(data)
        return data[:len(data) - FX_PAGESIZE * unused_pages]

# Get the save data which might be packed with a sketch (for FX-enabled programs!)
def get_savepart_raw(fulldata, index):
    spage = get_save_page(fulldata, index)
    if spage == 0xFFFF:
        return bytearray()
    else:
        return fulldata[spage*FX_PAGESIZE:index + get_slot_size_bytes(fulldata, index)]

def get_meta_parsed(fulldata, index):
    meta = fulldata[index+META_HEADER_INDEX:index+META_HEADER_INDEX+META_HEADER_SIZE]
    ppage = get_program_page(fulldata, index)
    values = meta.split(b'\x00')
    def mval(index):
        return values[index].decode('utf-8', 'ignore') if index < len(values) else ""
    if ppage == 0xFFFF:
        # This is a category, the values are title and info
        return FxSlotMeta(mval(0), "", "", mval(1))
    else:
        # This is a program, the values are in order
        return FxSlotMeta(mval(0), mval(1), mval(2), mval(3))
    

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

def embedded_save_size(data: bytearray) -> int:
    """Detect the size of an embedded save, return size in bytes. 
    
    Note that there are instances where an embedded save may be strangely aligned and detection fails,
    but I haven't run into this in any valid fx data yet."""
    unused_pages = count_unused_pages(data)
    if unused_pages >= (SAVE_ALIGNMENT // FX_PAGESIZE):
        return (unused_pages - (unused_pages % (SAVE_ALIGNMENT // FX_PAGESIZE))) * FX_PAGESIZE
    else:
        return 0

def parse(fulldata, report_progress = None) -> List[FxParsedSlot]:
    """ Given an entire FX binary, parse absolutely everything out of it (in slot format) """

    logging.debug(f"Full parsing FX cart ({len(fulldata)} bytes)")
    dindex = 0
    result = []

    while dindex < len(fulldata)-1:
        if not is_slot(fulldata, dindex):
            break

        slotsize = get_slot_size_bytes(fulldata, dindex)

        result.append(FxParsedSlot(
            get_category(fulldata, dindex), 
            get_title_image_raw(fulldata, dindex),
            # What about parsing the program bin? UGH! Most of the time we want the raw, not the parsed, someone else can do that
            get_program_raw(fulldata, dindex), 
            get_datapart_raw(fulldata, dindex),
            get_savepart_raw(fulldata, dindex),
            get_meta_parsed(fulldata, dindex)
        ))

        dindex += slotsize

        if report_progress:
            report_progress(dindex, len(fulldata))

    logging.info(f"Fully parsed {(len(result))} program sections")

    return result


def fix_parsed_slots(parsed_slots: List[FxParsedSlot]):
    """ Forcibly reassign all the categories, make sure first slot is a category, fill empty images with all 0's """
    category = -1
    count = 0
    if len(parsed_slots) < 2:
        raise Exception("Not enough items in the cart! Must have at least two categories (bootloader requirement)")
    for slot in parsed_slots:
        if slot.is_category():
            category += 1
        elif count == 0 or count == 1:
            raise Exception("First two items MUST be a category!")
        if not slot.image_raw or len(slot.image_raw) == 0:
            slot.image_raw = bytearray(SCREEN_BYTES) # This means, if you don't provide an image, it will be a black screen
        slot.category = category
        count += 1

def compile_single(slot: FxParsedSlot, currentpage = 0, previouspage = 0xFFFF, nextpage = 0) -> bytearray:
    """
    Compile a single slot (with the given page identifiers, VERY important) and return the result. 
    
    If you're just testing, the pages aren't required (but you won't get a valid frame)
    """
    if len(slot.image_raw) != SCREEN_BYTES:
        raise Exception(f"Title image for game {slot.meta.title} is incorrect size!! Expected: {SCREEN_BYTES}, was: {len(slot.image_raw)}")
    # All the raw data we're about to dump into the flashcart. Some may be modified later
    header = default_header()
    title = slot.image_raw
    program = pad_data(slot.program_raw, FX_PAGESIZE)  # WARN: YOU MUST ALWAYS PAD THE PROGRAM! You don't know who's supplying it!
    datafile = pad_data(slot.data_raw, FX_PAGESIZE) 
    savefile = pad_data(slot.save_raw, SAVE_ALIGNMENT) 
    # These are "post-padding" sizes. Program and data are padded to page size, save is padded to save size (4096)
    programsize = len(program)
    datasize = len(datafile)
    savesize = len(savefile)
    #don't flash last unused 128 bytes page
    program_flash_size = (programsize >> 7) - 1 if program[-FLASH_PAGESIZE:] == PROGRAM_NULLPAGE else programsize >> 7
    if program_flash_size > 0xFF: # Program size in half-pages is single byte
        raise Exception(f"Somehow, program is too large for game {slot.meta.title}! Might be a problem with the binary generator! Max size: {0xFFFF} half-pages, program was {program_flash_size}")
    id = sha256(program + datafile).digest()
    programpage = currentpage + PREAMBLE_PAGES
    datapage    = programpage + (programsize >> 8)  # Data comes after program, wherever it is
    alignpage   = datapage + (datasize >> 8)        # Calculate align page start even if alignment isn't used
    alignsize   = pad_size(alignpage, 16) * 256 if savesize > 0 else 0 # Only have alignment if save
    savepage    = alignpage + (alignsize >> 8)      # Save page might not be used, calculate it anyway
    total_binary_length = programsize + datasize + alignsize + savesize
    if total_binary_length & 0xFF:
        raise Exception(f"Sum of binary sizes is not page aligned for game {slot.meta.title}! Size: {total_binary_length}")
    slotpages   = PREAMBLE_PAGES + (total_binary_length >> 8)
    nextpage += slotpages
    header[7] = slot.category   #list number
    write_2byte_value(previouspage, header, PREVIOUS_PAGE_HEADER_INDEX)
    write_2byte_value(nextpage, header, NEXT_PAGE_HEADER_INDEX)
    write_2byte_value(slotpages, header, SLOT_SIZE_HEADER_INDEX)
    header[PROGRAM_SIZE_HEADER_INDEX] = program_flash_size
    # There IS a program, so let's set some more fields!
    if programsize > 0:
        write_2byte_value(programpage, header, PROGRAMPAGE_HEADER_INDEX)
        if datasize > 0:
            program[0x14] = 0x18    # IDK, some constants from the other program
            program[0x15] = 0x95
            write_2byte_value(datapage, program, 0x16)
            write_2byte_value(datapage, header, DATAPAGE_HEADER_INDEX)
            write_2byte_value(datasize >> 8, header, DATA_SIZE_HEADER_INDEX)
        if savesize > 0:
            program[0x18] = 0x18    # Some constants from the builder program
            program[0x19] = 0x95
            write_2byte_value(savepage, program, 0x1a)
            write_2byte_value(savepage, header, SAVEPAGE_HEADER_INDEX)
        header[25:57] = id  # NOTE: hash only used if program set!
        stringdata = (slot.meta.title.encode('utf-8') + b'\0' + slot.meta.version.encode('utf-8') + b'\0' +
                        slot.meta.developer.encode('utf-8') + b'\0' + slot.meta.info.encode('utf-8') + b'\0')
    else:
        stringdata = slot.meta.title.encode('utf-8') + b'\0' + slot.meta.info.encode('utf-8') + b'\0'
    if len(stringdata) > META_HEADER_SIZE:
        stringdata = stringdata[:META_HEADER_SIZE]  
    header[57:57 + len(stringdata)] = stringdata
    if len(header) != HEADER_LENGTH:
        raise Exception(f"Somehow, header length for {slot.meta.title} was not {HEADER_LENGTH}!")
    if len(program):
        patch_success, message = patch_menubuttons(program)
        if not patch_success:
            logging.warning(f"Couldn't patch menu to return to bootloader for {slot.meta.title}: {message}")
    return header + title + program + datafile + bytearray(b'\xFF' * alignsize) + savefile

def compile(parsed_slots: List[FxParsedSlot],  report_progress = None):
    """
    Compile the given parsed data of an arduboy cart back into bytes. 

    Taken mostly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/flashcart-builder.py
    """
    logging.debug(f"Compiling flashcart with {len(parsed_slots)} slots")
    # First, perform some checks and fixes. 
    fix_parsed_slots(parsed_slots)
    previouspage = 0xFFFF
    currentpage = 0
    nextpage = 0
    result = bytearray()
    games = 0
    categories = 0
    for slot in parsed_slots:
        slotbin = compile_single(slot, currentpage, previouspage, nextpage)
        result = result + slotbin
        nextpage += (len(slotbin) >> 8)
        if get_program_size_bytes(result, currentpage * FX_PAGESIZE) > 0:
            games += 1
        else:
            categories += 1
        previouspage = currentpage
        currentpage = nextpage
        if report_progress:
            report_progress(games + categories, len(parsed_slots))
    if nextpage < 65536:
        result += bytearray(b'\xFF' * 256)
    logging.info(f"Compiled fx flashcart, {len(result)} bytes, {games} games, {categories} categories")
    return result
