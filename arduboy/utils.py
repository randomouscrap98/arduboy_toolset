from hashlib import sha256
import logging
import arduboy.arduhex
import arduboy.fxcart

from arduboy.constants import *
from PIL import Image

LCDBOOTPROGRAM = b"\xD5\xF0\x8D\x14\xA1\xC8\x81\xCF\xD9\xF1\xAF\x20\x00"

MENUBUTTONPATCH = b'\x0f\x92\x0f\xb6\x8f\x93\x9f\x93\xef\x93\xff\x93\x80\x91\xcc\x01'+ \
                  b'\x8d\x5f\x8d\x37\x08\xf0\x8d\x57\x80\x93\xcc\x01\xe2\xe4\xf3\xe0'+ \
                  b'\x80\x81\x8e\x4f\x80\x83\x91\x81\x9f\x4f\x91\x83\x82\x81\x8f\x4f'+ \
                  b'\x82\x83\x83\x81\x8f\x4f\x83\x83\xed\xec\xf1\xe0\x80\x81\x8f\x5f'+ \
                  b'\x80\x83\x81\x81\x8f\x4f\x81\x83\x82\x81\x8f\x4f\x82\x83\x83\x81'+ \
                  b'\x8f\x4f\x83\x83\x8f\xb1\x8f\x60\x66\x99\x1c\x9b\x88\x27\x8f\x36'+ \
                  b'\x81\xf4\x80\x91\xFF\x0A\x98\x1b\x96\x30\x68\xf0\xe0\xe0\xf8\xe0'+ \
                  b'\x87\xe7\x80\x83\x81\x83\x88\xe1\x80\x93\x60\x00\xf0\x93\x60\x00'+ \
                  b'\xff\xcf\x90\x93\xFF\x0A\xff\x91\xef\x91\x9f\x91\x8f\x91\x0f\xbe'+ \
                  b'\x0f\x90\x18\x95'

# Special constants for menu button patch
MBP_fract_lds = 14
MBP_fract_sts = 26
MBP_millis_r30 = 28
MBP_millis_r31 = 30
MBP_overflow_r30 = 56
MBP_overflow_r31 = 58

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

# Attempt to patch the given binary program (single program!) to add the
# bootloader "return to menu" button combo. Taken as-is from 
# https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/flashcart-builder.py
def patch_menubuttons(program):
    if len(program) < 256: 
        return ''
    vector_23 = (program[0x5E] << 1) | (program[0x5F]  << 9) #ISR timer0 vector addr
    p = vector_23
    l = 0
    lds = 0
    branch = 0
    timer0_millis = 0 
    timer0_fract  = 0
    timer0_overflow_count = 0
    while p < (len(program) - 2):
        p += 2 #handle 2 byte instructions
        if program[p-2:p] == b'\x08\x95': #ret instruction
            l = -1
            break
        if (program[p-1] & 0xFC == 0xF4) & (program[p-2] & 0x07 == 0x00): # brcc instruction may jump beyond reti
            branch = ((program[p-1] & 0x03) << 6) + ((program[p-2] & 0xf8) >> 2)
            if branch < 128:
                branch = p + branch
            else:
                branch = p -256 + branch
        if program[p-2:p] == b'\x18\x95': #reti instruction
            l = p - vector_23
            if p > branch: # there was no branch beyond reti instruction
                break
        if l != 0: #branced beyond reti, look for rjmp instruction
            if program[p-1] & 0xF0 == 0xC0:
                l = p - vector_23
                break
        #handle 4 byte instructions
        if (program[p-1] & 0xFE == 0x90)  & (program[p-2] & 0x0F == 0x00): # lds instruction
            lds +=1
            if lds == 1:
                timer0_millis = program[p] | ( program[p+1] << 8)
            elif lds == 5:
                timer0_fract = program[p] | ( program[p+1] << 8)
            elif lds == 6:
                timer0_overflow_count = program[p] | ( program[p+1] << 8)
            p +=2
        if (program[p-1] & 0xFE == 0x92) & (program[p-2] & 0x0F == 0x00): # sts instruction
            p +=2
    if l == -1:
        return 'No menu patch applied. ISR contains subroutine.'
    elif l < len(MENUBUTTONPATCH):
        return 'No menu patch applied. ISR size too small ({} bytes)'.format(l)
    elif (timer0_millis == 0) | (timer0_fract == 0) | (timer0_overflow_count == 0):
        return 'No menu patch applied. Custom ISR in use.'
    else:
        #patch the new ISR code with 'hold UP + DOWN for 2 seconds to start bootloader menu' feature
        program[vector_23 : vector_23+len(MENUBUTTONPATCH)] = MENUBUTTONPATCH
        #fix timer variables
        program[vector_23 + MBP_fract_lds + 0] = timer0_fract & 0xFF
        program[vector_23 + MBP_fract_lds + 1] = timer0_fract >> 8
        program[vector_23 + MBP_fract_sts + 0] = timer0_fract & 0xFF
        program[vector_23 + MBP_fract_sts + 1] = timer0_fract >> 8
        program[vector_23 + MBP_millis_r30 + 0] = 0xE0 | (timer0_millis >> 0) & 0x0F
        program[vector_23 + MBP_millis_r30 + 1] = 0xE0 | (timer0_millis >> 4) & 0x0F
        program[vector_23 + MBP_millis_r31 + 0] = 0xF0 | (timer0_millis >> 8) & 0x0F
        program[vector_23 + MBP_millis_r31 + 1] = 0xE0 | (timer0_millis >>12) & 0x0F
        program[vector_23 + MBP_overflow_r30 +0] = 0xE0 | (timer0_overflow_count >> 0) & 0x0F
        program[vector_23 + MBP_overflow_r30 +1] = 0xE0 | (timer0_overflow_count >> 4) & 0x0F
        program[vector_23 + MBP_overflow_r31 +0] = 0xF0 | (timer0_overflow_count >> 8) & 0x0F
        program[vector_23 + MBP_overflow_r31 +1] = 0xE0 | (timer0_overflow_count >>12) & 0x0F
        return 'Menu patch applied'


# Convert a block of bytes (should be 1024) to a PILlow image
def bin_to_pilimage(byteData):
    byteLength = len(byteData)
    if byteLength != SCREEN_BYTES:
        raise Exception(f"Image binary not right size! Expected {SCREEN_BYTES} got {byteLength}")
    pixels = bytearray(SCREEN_WIDTH * SCREEN_HEIGHT)
    for b in range(0, byteLength):
        for i in range(0, 8):
            yPos = b//SCREEN_WIDTH*8+i
            xPos = b%SCREEN_WIDTH
            pixels[yPos * SCREEN_WIDTH + xPos] = 255 * bytebit(byteData[b], i)

    img = Image.frombytes("L", (SCREEN_WIDTH, SCREEN_HEIGHT), bytes(pixels))

    return img

# Taken almost directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/flashcart-builder.py
def pilimage_to_bin(image: Image):
    binimg = image.convert("1")
    width, height  = binimg.size
    if (width != SCREEN_WIDTH) or (height != SCREEN_HEIGHT) :
        if height // (width // SCREEN_WIDTH) != SCREEN_HEIGHT:
            raise Exception("Image dimensions incorrect! Must be a multiple of 128x64")
        else:
            binimg = binimg.resize((SCREEN_WIDTH,SCREEN_HEIGHT), Image.NEAREST)
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
    

# Convert a block of bytes (should be pre-filled with the correct data) to a single "arduhex" 
# string. Taken almost directly from 
# https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/flashcart-decompiler.py
def bin_to_arduhex(byteData):
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

# Convert an in-memory arduhex string into pure bytes for writing to a flashcart. Note
# that this is STRICTLY different than parsing an arduhex string for dumping to serial!
# Taken directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/flashcart-builder.py
# TODO: Some of this "arduhex" parsing code needs to be refactored! It's confusing why
# one would produce a "trimmed" binary and the other a "parsed object" with information
# ABOUT trimming but the data not trimmed!!
def arduhex_to_bin(arduhex_str):
    # result = arduboy.arduhex.parse(arduboy.arduhex.ArduboyParsed("", rawhex=arduhex_str))
    # return result.flash_data
    records = arduhex_str.splitlines()
    bytes = bytearray(b'\xFF' * 29 * 1024)
    flash_end = 0
    for rcd in records :
        if rcd[0] == ":" :
            rcd_len  = int(rcd[1:3],16)
            rcd_typ  = int(rcd[7:9],16)
            rcd_addr = int(rcd[3:7],16)
            checksum = int(rcd[9+rcd_len*2:11+rcd_len*2],16)
            if (rcd_typ == 0) and (rcd_len > 0) :
                flash_addr = rcd_addr
                for i in range(1,9+rcd_len*2, 2) :
                    byte = int(rcd[i:i+2],16)
                    checksum += byte
                    if i >= 9:
                        bytes[flash_addr] = byte
                        flash_addr += 1
                if flash_addr > flash_end:
                    flash_end = flash_addr
                if checksum  & 0xFF != 0 :
                    raise Exception(f"Hex file contains errors! Checksum fail: {checksum}")
    flash_end = (flash_end + 255) & 0xFF00
    return bytes[0:flash_end]


def new_parsed_slot_from_category(title, info = "", image = None, category_id = 0):
    return arduboy.fxcart.FxParsedSlot(
        category_id,
        image,
        bytearray(),
        bytearray(),
        bytearray(),
        arduboy.fxcart.FxSlotMeta(title, "", "", info)
    )
    # sha256(bytearray()).digest(),

# Given a parsed arduhex file, generate a reasonable slot file
def new_parsed_slot_from_arduboy(parsed: arduboy.arduhex.ArduboyParsed):
    return arduboy.fxcart.FxParsedSlot(
        0, # Might not matter
        parsed.image,
        arduhex_to_bin(parsed.rawhex), # The three main slot data fields are all stored raw in FxParsedSlot, including program.
        parsed.data_raw,
        parsed.save_raw,
        arduboy.fxcart.FxSlotMeta(parsed.title if parsed.title else parsed.original_filename, parsed.version, parsed.developer, parsed.info)
    )
