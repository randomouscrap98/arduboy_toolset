# Given a connected serial port, exit the bootloader
import logging
import time
from arduboy.device import MANUFACTURERS,FXBLOCKSIZE,FXPAGES_PER_BLOCK,FXPAGESIZE
from dataclasses import dataclass


def exit_bootloader(s_port):
    s_port.write(b"E")
    s_port.read(1)

def get_version(s_port):
    s_port.write(b"V")
    return int(s_port.read(2))

def get_jedec_id(s_port):
    s_port.write(b"j")
    jedec_id = s_port.read(3)
    time.sleep(0.5)   #  Why is this necessary? This sucks... maybe weird manufacturer quirks?
    s_port.write(b"j")
    jedec_id2 = s_port.read(3)
    if jedec_id2 != jedec_id or jedec_id == b'\x00\x00\x00' or jedec_id == b'\xFF\xFF\xFF':
        raise Exception(f"No flash cart detected on port {s_port.port}")
    return bytearray(jedec_id)

@dataclass
class JedecInfo:
    id: bytearray
    capacity: int
    manufacturer: str

    def __str__(self):
        return "0x{:02X}{:02X}{:02X} - {} ({} KiB)".format(self.id[0],self.id[1],self.id[2], self.manufacturer, 
            self.capacity // 1024 if self.manufacturer != "unknown" else "???")

# Get parsed jedec info from device. Will throw exception if device has no jedec info
def get_jedec_info(s_port):
    jedec_id = get_jedec_id(s_port)
    if jedec_id[0] in MANUFACTURERS.keys():
        manufacturer = MANUFACTURERS[jedec_id[0]]
    else:
        manufacturer = "unknown"
    return JedecInfo(jedec_id, 1 << jedec_id[2], manufacturer)

# Given a connected serial port, see if bootloader is "caterina"
def is_caterina(s_port):
    version = get_version(s_port)   #get bootloader software version
    if version == 10:       #original caterina 1.0 bootloader
        s_port.write(b"r")  #read lock bits
        return ord(s_port.read(1)) & 0x10 != 0
    return False

# Flash the given arduboy hex file to the given connected arduboy. Can report progress
# by giving a function that accepts a "current" and "total" parameter.
def flash_arduhex(arduhex, s_port, report_progress: None):
    # Just like fx flash rejects non-fx chips and bad bootloaders, this one too will reject "bad" bootloader
    if arduhex.overwrites_caterina and is_caterina(s_port):
        raise Exception("Upload will likely corrupt the bootloader.")
    logging.info("Flashing {} bytes. ({} flash pages)".format(arduhex.flash_page_count * 128, arduhex.flash_page_count))
    flash_page = 0
    for i in range (256):
        if arduhex.flash_page_used[i]:
            s_port.write(bytearray([ord("A"), i >> 2, (i & 3) << 6]))
            s_port.read(1)
            s_port.write(b"B\x00\x80F")
            s_port.write(arduhex.flash_data[i * 128 : (i + 1) * 128])
            s_port.read(1)
            flash_page += 1
            if report_progress:
                report_progress(flash_page, arduhex.flash_page_count)

# Verify that the given arduboy hex file is correctly flashed to the given connected arduboy. Can report progress
# by giving a function that accepts a "current" and "total" parameter.
def verify_arduhex(arduhex, s_port, report_progress: None):
    logging.info("Verifying {} bytes. ({} flash pages)".format(arduhex.flash_page_count * 128, arduhex.flash_page_count))
    flash_page = 0
    for i in range (256) :
        if arduhex.flash_page_used[i] :
            s_port.write(bytearray([ord("A"), i >> 2, (i & 3) << 6]))
            s_port.read(1)
            s_port.write(b"g\x00\x80F")
            if s_port.read(128) != arduhex.flash_data[i * 128 : (i + 1) * 128] :
                raise Exception("Verify failed at address {:04X}. Upload unsuccessful.".format(i * 128))
            flash_page += 1
            if report_progress:
                report_progress(flash_page, arduhex.flash_page_count)

# Read the 1k eeprom as a byte array. Cannot report progress (too small)
def read_eeprom(s_port):
    logging.debug("Reading 1K EEPROM data...")
    s_port.write(b"A\x00\x00")
    s_port.read(1)
    s_port.write(b"g\x04\x00E")
    eepromdata = bytearray(s_port.read(1024))
    return eepromdata

# Write the 1k eeprom as a byte array. Throws exception if provided data not right size. 
# Cannot report progress (too small)
def write_eeprom(eepromdata, s_port):
    logging.debug("Writing 1K EEPROM data...")
    if len(eepromdata) != 1024:
        raise Exception("Provided EEPROM data does not contain exactly 1K (1024 bytes)")
    s_port.write(b"A\x00\x00")
    s_port.read(1)
    s_port.write(b"B\x04\x00E")
    s_port.write(eepromdata)
    s_port.read(1)

# Erase entire eeprom (apparently means all 0xFF). Cannot report progress (too small)
def erase_eeprom(s_port):
    s_port.write(b"A\x00\x00")
    s_port.read(1)
    s_port.write(b"B\x04\x00E")
    s_port.write(b"\xFF" * 1024)
    s_port.read(1)

# Both verify the version AND retrieve/verify the jedec information. This is used for all
# FX operations, so it's useful to mix them all together.
def get_and_verify_jdec_bootloader(s_port):
    if get_version(s_port) < 13:
        raise Exception("Bootloader has no flash cart support. Can't write FX flash!")
    jedec_info = get_jedec_info(s_port)
    logging.info(f"JDEC info: {jedec_info}")
    return jedec_info

# Write the given flash blob (of exact size?) to the given exact page offset in fx.
# Taken almost verbatim from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/flashcart-writer.py.
# This one strays from the design of the other flashing functions because the verification is builtin.
def flash_fx(flashdata, pagenumber, s_port, verify = True, report_progress = None):

    ## detect flash cart ## (apparently jdec info not used here)
    get_and_verify_jdec_bootloader(s_port)
    
    start=time.time()

    # when starting partially in a block, preserve the beginning of old block data
    if pagenumber % FXPAGES_PER_BLOCK:
        blocklen  = pagenumber % FXPAGES_PER_BLOCK * FXPAGESIZE
        blockaddr = pagenumber // FXPAGES_PER_BLOCK * FXPAGES_PER_BLOCK
        #read partial block data start
        s_port.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
        s_port.read(1)
        s_port.write(bytearray([ord("g"), (blocklen >> 8) & 0xFF, blocklen & 0xFF,ord("C")]))
        flashdata = s_port.read(blocklen) + flashdata
        pagenumber = blockaddr
      
    # when ending partially in a block, preserve the ending of old block data
    if len(flashdata) % FXBLOCKSIZE:
        blocklen = FXBLOCKSIZE - len(flashdata) % FXBLOCKSIZE
        blockaddr = pagenumber + len(flashdata) // FXPAGESIZE
        #read partial block data end
        s_port.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
        s_port.read(1)
        s_port.write(bytearray([ord("g"), (blocklen >> 8) & 0xFF, blocklen & 0xFF,ord("C")]))
        flashdata += s_port.read(blocklen)

    ## write to flash cart ##
    blocks = len(flashdata) // FXBLOCKSIZE
    logging.info("Flashing {} blocks to FX in port {}".format(blocks, s_port.port))

    for block in range (blocks):
        if (block & 1 == 0) or verify:
            s_port.write(b"x\xC2") #RGB LED RED, buttons disabled
        else:  
            s_port.write(b"x\xC0") #RGB LED OFF, buttons disabled
        s_port.read(1)
        blockaddr = pagenumber + block * FXBLOCKSIZE // FXPAGESIZE
        blocklen = FXBLOCKSIZE
        #write block 
        s_port.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
        s_port.read(1)
        s_port.write(bytearray([ord("B"), (blocklen >> 8) & 0xFF, blocklen & 0xFF,ord("C")]))
        s_port.write(flashdata[block * FXBLOCKSIZE : block * FXBLOCKSIZE + blocklen])
        s_port.read(1)
        if verify:
            s_port.write(b"x\xC1") #RGB BLUE RED, buttons disabled
            s_port.read(1)
            s_port.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
            s_port.read(1)
            s_port.write(bytearray([ord("g"), (blocklen >> 8) & 0xFF, blocklen & 0xFF,ord("C")]))
            if s_port.read(blocklen) != flashdata[block * FXBLOCKSIZE : block * FXBLOCKSIZE + blocklen]:
                raise Exception("FX verify failed at address {:04X}. Upload unsuccessful.".format(blockaddr))
        if report_progress:
            report_progress(block + 1, blocks)
    
    #write complete  
    s_port.write(b"x\x44")#RGB LED GREEN, buttons enabled
    s_port.read(1)
    time.sleep(0.5)    
    logging.info("Wrote {} blocks in {} seconds".format(blocks, round(time.time() - start,2)))

# Read FX data and dump to the given file. Can report progress same as arduhex functions. 
# This is once again different than the arduhex function in that it writes directly to a file.
# Didn't want to disturb the original implementation
def backup_fx(s_port, filename, report_progress = None):

    ## detect flash cart ## 
    jedec_info = get_and_verify_jdec_bootloader(s_port)

    start=time.time()
    
    blocks = jedec_info.capacity // FXBLOCKSIZE
    logging.info(f"Reading entire FX in port {s_port.port} into file {filename}")

    # Just like original function, it writes directly to the file given.
    with open(filename,"wb") as binfile:
        for block in range (0, blocks):
            if block & 1:
                s_port.write(b"x\xC0") #RGB BLUE OFF, buttons disabled
            else:  
                s_port.write(b"x\xC1") #RGB BLUE RED, buttons disabled
            s_port.read(1)      

            blockaddr = block * FXBLOCKSIZE // FXPAGESIZE

            s_port.write("A".encode())
            s_port.write(bytearray([blockaddr >> 8, blockaddr & 0xFF]))
            s_port.read(1)

            blocklen = FXBLOCKSIZE

            s_port.write("g".encode())
            s_port.write(bytearray([(blocklen >> 8) & 0xFF, blocklen & 0xFF]))

            s_port.write("C".encode())
            contents=s_port.read(blocklen)
            binfile.write(contents)

            if report_progress:
                report_progress(block + 1, blocks)

    s_port.write(b"x\x44")  #RGB LED GREEN, buttons enabled
    s_port.read(1)
    time.sleep(0.5)
    logging.info("Read {} blocks in {} seconds".format(blocks, round(time.time() - start,2)))