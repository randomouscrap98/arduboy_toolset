"""
A collection of simple functions used for non-specific tasks in Arduboy

This file should not have any dependent or specific code. i.e. it should not 
be tied to FX, Arduhex, images, devices, patches, serial, etc. It is only
for self-contained, simple functions which are helpful in any Arduboy task.
"""

from io import BytesIO, StringIO
from intelhex import IntelHex
from .constants import *

def pad_data(data: bytearray, multsize, pad = b'\xFF'):
    """Pad data to a multiple of the given size.

    For instance, if data is 245 but multsize is 256, it is padded up to 256 with the given pad data.
    If data is 400 and multsize is 256, it is padded up to 512

    Returns: 
        padded data
    """
    if len(data) % multsize: 
        data += pad * (multsize - (len(data) % multsize))
    return data

def pad_size(length: int, alignment: int):
    """Compute amount of padding to add to the given length of data for the given alignment
    
    For instance, if length is 245 but alignment is 256, 11 is returned
    
    Returns:
        amount of padding to make length be aligned to given alignment
    """
    if length % alignment:  # It is misaligned, to get it aligned, must know the difference
        return alignment - (length % alignment)
    else: # It is exactly aligned
        return 0 

def bytebit(byte: int, pos: int):
    """Get the bit at position
    
    Returns:
        The bit (1 or 0)
    """
    return (byte >> pos) & 1

def int_to_hex(integer: int, hexchars: int):
    """Get hexstring for given integer (without 0x)

    Returns:
        Integer as hex with given amount of characters (prepadded with 0)
    """
    return hex(integer).replace("0x", "").upper().zfill(hexchars)

def count_unused_pages(data: bytearray):
    """Get the number of unused pages (Arduboy/FX size) at the end of the given data block
    
    Returns:
        count of unused pages
    """
    last_FF_index = 0 # Loop will exit without assignment if ALL are 0xFF
    for i in range(len(data) - 1, -1, -1):
        if data[i] != 0xFF:
            last_FF_index = i + 1 # If the very last byte isn't FF, index will be outside range, math still works
            break
    unused_pages = (len(data) - last_FF_index) // FX_PAGESIZE
    return unused_pages

def hex_to_bin(rawhex: str) -> bytearray:
    """Convert raw hex string (intel hex format) to raw bytearray
    
    Returns:
        Binary from hex, exactly as read
    """
    buffer = StringIO(rawhex)
    ihex = IntelHex(buffer)
    return bytearray(ihex.tobinarray()) # start=0, size=FLASH_SIZE))

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
