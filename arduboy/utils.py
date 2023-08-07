import logging

from arduboy.constants import *
from PIL import Image

LCDBOOTPROGRAM = b"\xD5\xF0\x8D\x14\xA1\xC8\x81\xCF\xD9\xF1\xAF\x20\x00"

# Pad data to a multiple of the given size. For instance, if data is 245 but multsize is
# 256, it is padded up to 256 with the given pad data. If data is 400 and multsize is 256,
# it is padded up to 512
def pad_data(data, multsize, pad = b'\xFF'):
    if len(data) % multsize: 
        data += pad * (multsize - (len(data) % multsize))
    return data

# Get the bit at position (1 or 0)
def bytebit(byte, pos):
    return (byte >> pos) & 1

# Return integer as hex string with the given number of hex characters (prepadded with 0)
def int_to_hex(integer, hexchars):
    return hex(integer).replace("0x", "").upper().zfill(hexchars)

# Given binary data, patch EVERY instance of the lcd boot program for ssd1309
# Taken almost directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/uploader.py.
def patch_all_ssd1309(flashdata):
    logging.debug("Patching all LCD boot programs for SSD1309 displays")
    lcdBootProgram_addr = 0
    found = 0
    while lcdBootProgram_addr >= 0:
      lcdBootProgram_addr = flashdata.find(LCDBOOTPROGRAM, lcdBootProgram_addr)
      if lcdBootProgram_addr >= 0:
        flashdata[lcdBootProgram_addr+2] = 0xE3;
        flashdata[lcdBootProgram_addr+3] = 0xE3;
        found += 1
    return found

# Given binary data, patch EVERY instance of wrong LED polarity for Micro
# Taken directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/uploader.py
def patch_microled(flashdata):
    for i in range(0,FLASHSIZE-4,2):
        if flashdata[i:i+2] == b'\x28\x98':   # RXLED1
            flashdata[i+1] = 0x9a
        elif flashdata[i:i+2] == b'\x28\x9a': # RXLED0
            flashdata[i+1] = 0x98
        elif flashdata[i:i+2] == b'\x5d\x98': # TXLED1
            flashdata[i+1] = 0x9a
        elif flashdata[i:i+2] == b'\x5d\x9a': # TXLED0
            flashdata[i+1] = 0x98
        elif flashdata[i:i+4] == b'\x81\xef\x85\xb9' : # Arduboy core init RXLED port
            flashdata[i] = 0x80
        elif flashdata[i:i+4] == b'\x84\xe2\x8b\xb9' : # Arduboy core init TXLED port
            flashdata[i+1] = 0xE0

# Convert a block of bytes (should be 1024) to a PILlow image
def bin_to_pilimage(byteData):
    byteLength = len(byteData)
    pixels = bytearray(8192)
    for b in range(0, byteLength):
        for i in range(0, 8):
            yPos = b//128*8+i
            xPos = b%128
            pixels[yPos * 128 + xPos] = 255 * bytebit(byteData[b], i)

    img = Image.frombytes("L", (128, 64), bytes(pixels))

    return img

# Convert a block of bytes (should be pre-filled with the correct data) to a string 
# that is a hex file (for Arduboy). Taken directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/flashcart-decompiler.py
def bin_to_hexfile(byteData):
    byteLength = len(byteData)

    hexData = []
    for byteNum in range(0, byteLength, 16):
        hexLine = ":10" + int_to_hex(byteNum, 4) + "00"
        for i in range(0, 16):
            if byteNum+i > byteLength-1:
                break
            hexLine += int_to_hex(byteData[byteNum+i], 2)
        lineSum = 0
        for i in range(1, 41, 2):
            hexByte = hexLine[i] + hexLine[i+1]
            lineSum += int(hexByte, 16)

        checkSum = 256-lineSum%256
        if checkSum == 256:
            checkSum = 0
        hexLine += int_to_hex(checkSum, 2)
        hexData.append(hexLine)

    if byteLength%16 > 0:
        lineSum = (byteLength%16) + (byteLength-byteLength%16)
        hexLine = ":" + int_to_hex(byteLength%16, 2) + int_to_hex(byteLength-byteLength%16, 4) + "00"
        for i in range(0, byteLength%16):
            lineSum += int(byteData[byteLength-byteLength%16+i])
            hexLine += int_to_hex(int(byteData[byteLength-byteLength%16+i]))
        hexLine += int_to_hex(256-lineSum%256, 2)
        hexData.append(hexLine)

    fullHexString = ""
    for hexLine in range(0, len(hexData)):
        fullHexString += hexData[hexLine]
        if hexLine != len(hexData)-1:
            fullHexString += "\n"

    return fullHexString