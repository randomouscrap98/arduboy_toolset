from arduboy.constants import *

import logging

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

CONTRAST_NOCHANGE = None
CONSTRAST_NORMAL = 0xCF
CONTRAST_DIM = 0x7F
CONTRAST_DIMMER = 0x2F
CONTRAST_DIMMEST = 0x00
CONTRAST_HIGHEST = 0xFF

# Special constants for menu button patch
MBP_fract_lds = 14
MBP_fract_sts = 26
MBP_millis_r30 = 28
MBP_millis_r31 = 30
MBP_overflow_r30 = 56
MBP_overflow_r31 = 58

# Attempt to patch the given binary program (single program!) to add the
# bootloader "return to menu" button combo. Taken as-is from 
# https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/flashcart-builder.py
# NOTE: This patch doesn't seem to change the size of the program, it's done "in-place"
def patch_menubuttons(program):
    if len(program) < 256: 
        return (False, "Program too short")
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
        return (False,'No menu patch applied. ISR contains subroutine.')
    elif l < len(MENUBUTTONPATCH):
        return (False,'No menu patch applied. ISR size too small ({} bytes)'.format(l))
    elif (timer0_millis == 0) | (timer0_fract == 0) | (timer0_overflow_count == 0):
        return (False, 'No menu patch applied. Custom ISR in use.')
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
        return (True, 'Menu patch applied')


# Given binary data, apply various screen-related patches
def patch_all_screen(flashdata: bytearray, ssd1309: bool = False, contrast: int = None):
    lcdBootProgram_addr = 0
    while lcdBootProgram_addr >= 0:
      lcdBootProgram_addr = flashdata.find(LCDBOOTPROGRAM[:7], lcdBootProgram_addr)
      if lcdBootProgram_addr >= 0 and flashdata[lcdBootProgram_addr+8:lcdBootProgram_addr+13] == LCDBOOTPROGRAM[8:]:
        if ssd1309:
          flashdata[lcdBootProgram_addr+2] = 0xE3
          flashdata[lcdBootProgram_addr+3] = 0xE3
        if contrast is not None:
          flashdata[lcdBootProgram_addr+7] = contrast

# Given binary data, patch EVERY instance of wrong LED polarity for Micro
# Taken directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/uploader.py
def patch_microled(flashdata: bytearray):
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
