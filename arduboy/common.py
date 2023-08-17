from arduboy.constants import *

from PIL import Image

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

# Convert a block of arduboy image bytes (should be 1024) to a PILlow image
def bin_to_pilimage(byteData, raw = False):
    byteLength = len(byteData)
    if byteLength != SCREEN_BYTES:
        raise Exception(f"Image binary not right size! Expected {SCREEN_BYTES} got {byteLength}")

    pixels = bytearray(SCREEN_WIDTH * SCREEN_HEIGHT)
    for b in range(0, len(pixels)):
        ob = b >> 3
        pixels[((((ob >> 7) << 3)+(b & 7)) << 7) + (ob & 127)] = 255 * ((byteData[ob] >> (b & 7)) & 1)
    
    if raw:
        return pixels

    img = Image.frombytes("L", (SCREEN_WIDTH, SCREEN_HEIGHT), pixels)

    return img

# Convert any PIL image with any dimensions into an arduboy binary image. Note: this means
# it could be stretched and dithered and whatever.
# Taken almost directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/flashcart-builder.py
def pilimage_to_bin(image: Image):
    binimg = convert_titlescreen(image)
    width, height  = binimg.size
    pixels = list(binimg.getdata())
    bytes = bytearray(int((height // 8) * width))
    i = 0
    b = 0
    for y in range (0,height,8):
        for x in range (0,width):
            for p in range (0,8):
                b = b >> 1  
                if pixels[(y + p) * width + x] > 0:
                    b |= 0x80
            bytes[i] = b
            i += 1
    return bytes
    

# Try to get the given image in the right format and size for Arduboy. Still returns a PIL image.
def convert_titlescreen(image):
    width, height = image.size
    # Actually for now I'm just gonna stretch it, I don't care! Hahaha TODO: fix this
    if width != SCREEN_WIDTH or height != SCREEN_HEIGHT:
        image = image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.NEAREST)
    image = image.convert("1") # Do this after because it's probably better AFTER nearest neighbor
    return image
