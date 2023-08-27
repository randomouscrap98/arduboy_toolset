from arduboy.constants import *

# Pad data to a multiple of the given size. For instance, if data is 245 but multsize is
# 256, it is padded up to 256 with the given pad data. If data is 400 and multsize is 256,
# it is padded up to 512
def pad_data(data: bytearray, multsize, pad = b'\xFF'):
    if len(data) % multsize: 
        data += pad * (multsize - (len(data) % multsize))
    return data

# Return the amount of padding to add to the given length of data if you wish for the 
# given alignment. For instance, if length is 245 but alignment is 256, 11 is returned
def pad_size(length, alignment):
    if length % alignment:  # It is misaligned, to get it aligned, must know the difference
        return alignment - (length % alignment)
    else: # It is exactly aligned
        return 0 

# Get the bit at position (1 or 0)
def bytebit(byte, pos):
    return (byte >> pos) & 1

# Return integer as hex string with the given number of hex characters (prepadded with 0)
def int_to_hex(integer, hexchars):
    return hex(integer).replace("0x", "").upper().zfill(hexchars)

# Find the number of unused pages at the end of the given data block
def count_unused_pages(data):
    last_FF_index = 0 # Loop will exit without assignment if ALL are 0xFF
    for i in range(len(data) - 1, -1, -1):
        if data[i] != 0xFF:
            last_FF_index = i + 1 # If the very last byte isn't FF, index will be outside range, math still works
            break
    unused_pages = (len(data) - last_FF_index) // FX_PAGESIZE
    return unused_pages
