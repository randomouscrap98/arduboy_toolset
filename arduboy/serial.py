# Given a connected serial port, exit the bootloader
import logging
import time
import io
import arduboy.common
import arduboy.arduhex

from arduboy.constants import *
from arduboy.device import MANUFACTURERS
from dataclasses import dataclass



# Mr.Blinky's scripts had some time for exiting. I assumed it was to read the screen in 
# his scripts, since it was 3 seconds. I removed it, and hope it's not necessary
# in case, I have also included a small timeout here too. If I get confirmation the exit time
# is just to read printed output, I will reduce the time further.
def exit_bootloader(s_port):
    s_port.write(b"E")
    s_port.read(1)
    s_port.close()

def exit_normal(s_port):
    #Do a cute little LED thing (that wastes half a second but whatever, it's cute)
    s_port.write(b"x\x46")#RGB LED GREEN + RED, buttons enabled
    s_port.read(1)
    time.sleep(0.5)    
    s_port.write(b"x\x40")#RGB LED off, buttons enabled
    s_port.read(1)
    s_port.close()

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

def address_command(page):
    """Get the set-address command for the given INTERNAL FLASH page (128 byte pages), it's nontrivial"""
    return bytearray([ord("A"), page >> 2, (page & 3) << 6])


@dataclass
class JedecInfo:
    id: bytearray
    capacity: int
    manufacturer: str

    def __str__(self):
        return "0x{:02X}{:02X}{:02X} - {} ({} KiB)".format(self.id[0],self.id[1],self.id[2], self.manufacturer, 
            self.capacity // 1024 if self.manufacturer != "unknown" else "???")
    
    def total_pages(self):
        return self.capacity // FX_PAGESIZE


# Get parsed jedec info from device. Will throw exception if device has no jedec info
def get_jedec_info(s_port) -> JedecInfo:
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

# Return the apparent (may be wrong) length of the bootloader
def bootloader_length(s_port):
    return  2048 + (2048 if is_caterina(s_port) else 1024)

def read_bootloader(s_port):
    blength = bootloader_length(s_port)
    logging.debug(f"Reading bootloader, length = {blength}")
    # Read the larger of the two bootloaders
    s_port.write(address_command(BOOTLOADER_CATERINA_PAGE))
    s_port.read(1)
    s_port.write(b"g\x10\x00F") # TODO: change this to a constructed command as well
    result = bytearray(s_port.read(0x1000))
    # Then return only a portion of it
    return result[-blength:]


# Flash the given arduboy hex file to the given connected arduboy. Can report progress
# by giving a function that accepts a "current" and "total" parameter.
def flash_arduhex(bindata: bytearray, s_port, report_progress: None):
    # Analyze the bindata
    bindata = arduboy.common.pad_data(bindata.copy(), FLASH_SIZE)
    analysis = arduboy.arduhex.analyze_sketch(bindata)
    logging.debug(f"Info on hex file: {analysis.total_pages} pages, is_caterina: {analysis.overwrites_caterina}")
    # Just like fx flash rejects non-fx chips and bad bootloaders, this one too will reject "bad" bootloader
    if analysis.overwrites_caterina and is_caterina(s_port):
        raise Exception("Upload will likely corrupt the bootloader.")
    logging.info("Flashing {} pages".format(analysis.total_pages))
    for i in range(analysis.total_pages): # (FLASH_PAGECOUNT):
        s_port.write(address_command(i))
        s_port.read(1)
        s_port.write(b"B\x00\x80F")
        s_port.write(bindata[i * FLASH_PAGESIZE: (i + 1) * FLASH_PAGESIZE])
        s_port.read(1)
        if report_progress:
            report_progress(i, analysis.total_pages)

# Read the sketch off arduboy. Does not strip unused bytes (but will strip bootloader if configured)
def backup_sketch(s_port, include_bootloader = False):
    logging.info("Reading sketch...")
    s_port.write(address_command(0))
    s_port.read(1)
    # Read the whole thing, we don't know how big the bootloader is yet (and it doesn't matter, just read the whole thing)
    s_port.write(b"g\x80\x00F")
    backupdata = bytearray(s_port.read(0x8000))
    if not include_bootloader:
        blength = bootloader_length(s_port)
        logging.debug(f"Stripping bootloader in sketch backup, length = {blength}")
        backupdata = backupdata[:-blength] # Strip the bootloader
    return backupdata

# Verify that the given arduboy hex file is correctly flashed to the given connected arduboy. Can report progress
# by giving a function that accepts a "current" and "total" parameter.
def verify_arduhex(bindata: bytearray, s_port, report_progress: None):
    analysis = arduboy.arduhex.analyze_sketch(bindata)
    logging.info("Verifying {} flash pages".format(analysis.total_pages))
    flash_page = 0
    for i in range (analysis.total_pages) :
        s_port.write(address_command(i)) # bytearray([ord("A"), i >> 2, (i & 3) << 6]))
        s_port.read(1)
        s_port.write(b"g\x00\x80F")
        if s_port.read(128) != bindata[i * 128 : (i + 1) * 128]:
            raise Exception("Verify failed at address {:04X}. Upload unsuccessful.".format(i * 128))
        flash_page += 1
        if report_progress:
            report_progress(flash_page, analysis.total_pages)

# Read the 1k eeprom as a byte array. Cannot report progress (too small)
def read_eeprom(s_port):
    logging.debug("Reading 1K EEPROM data...")
    s_port.write(address_command(0)) # b"A\x00\x00")
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
    s_port.write(address_command(0)) # b"A\x00\x00")
    s_port.read(1)
    s_port.write(b"B\x04\x00E")
    s_port.write(eepromdata)
    s_port.read(1)

# Erase entire eeprom (apparently means all 0xFF). Cannot report progress (too small)
def erase_eeprom(s_port):
    s_port.write(address_command(0)) # b"A\x00\x00")
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
def flash_fx(flashdata: bytearray, pagenumber: int, s_port, verify = True, report_progress = None):

    if not len(flashdata):
        raise Exception("No flash data provided!")

    info = get_and_verify_jdec_bootloader(s_port)
    flashdata = arduboy.common.pad_data(flashdata, FX_PAGESIZE)
    
    start=time.time()

    # If someone requested to write to the end of the flash, figure out the page number such that
    # it would encompass the whole data right at the end
    if pagenumber < 0:
        pagenumber = info.total_pages() - (len(flashdata) // FX_PAGESIZE)

    # when starting partially in a block, preserve the beginning of old block data
    if pagenumber % FX_PAGES_PER_BLOCK:
        blocklen  = pagenumber % FX_PAGES_PER_BLOCK * FX_PAGESIZE
        blockaddr = pagenumber // FX_PAGES_PER_BLOCK * FX_PAGES_PER_BLOCK
        #read partial block data start
        s_port.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
        s_port.read(1)
        s_port.write(bytearray([ord("g"), (blocklen >> 8) & 0xFF, blocklen & 0xFF,ord("C")]))
        flashdata = s_port.read(blocklen) + flashdata
        pagenumber = blockaddr
      
    # when ending partially in a block, preserve the ending of old block data
    if len(flashdata) % FX_BLOCKSIZE:
        blocklen = FX_BLOCKSIZE - len(flashdata) % FX_BLOCKSIZE
        blockaddr = pagenumber + len(flashdata) // FX_PAGESIZE
        #read partial block data end
        s_port.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
        s_port.read(1)
        s_port.write(bytearray([ord("g"), (blocklen >> 8) & 0xFF, blocklen & 0xFF,ord("C")]))
        flashdata += s_port.read(blocklen)

    ## write to flash cart ##
    blocks = len(flashdata) // FX_BLOCKSIZE
    logging.info("Flashing {} blocks to FX in port {}".format(blocks, s_port.port))

    for block in range (blocks):
        if (block & 1 == 0) or verify:
            s_port.write(b"x\xC2") #RGB LED RED, buttons disabled
        else:  
            s_port.write(b"x\xC0") #RGB LED OFF, buttons disabled
        s_port.read(1)
        blockaddr = pagenumber + block * FX_BLOCKSIZE // FX_PAGESIZE
        blocklen = FX_BLOCKSIZE
        #write block 
        s_port.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
        s_port.read(1)
        s_port.write(bytearray([ord("B"), (blocklen >> 8) & 0xFF, blocklen & 0xFF,ord("C")]))
        s_port.write(flashdata[block * FX_BLOCKSIZE : block * FX_BLOCKSIZE + blocklen])
        s_port.read(1)
        if verify:
            s_port.write(b"x\xC1") #RGB BLUE RED, buttons disabled
            s_port.read(1)
            s_port.write(bytearray([ord("A"), blockaddr >> 8, blockaddr & 0xFF]))
            s_port.read(1)
            s_port.write(bytearray([ord("g"), (blocklen >> 8) & 0xFF, blocklen & 0xFF,ord("C")]))
            if s_port.read(blocklen) != flashdata[block * FX_BLOCKSIZE : block * FX_BLOCKSIZE + blocklen]:
                raise Exception("FX verify failed at address {:04X}. Upload unsuccessful.".format(blockaddr))
        if report_progress:
            report_progress(block + 1, blocks)
    
    s_port.write(b"x\x40")#RGB LED off, buttons enabled
    s_port.read(1)
    logging.info("Wrote {} blocks in {} seconds".format(blocks, round(time.time() - start,2)))


# Read FX data and return the binary dump. Can report progress same as arduhex functions. 
# def backup_fx(s_port, filename, report_progress = None):
def backup_fx(s_port, report_progress = None):

    ## detect flash cart ## 
    jedec_info = get_and_verify_jdec_bootloader(s_port)

    start=time.time()
    
    blocks = jedec_info.capacity // FX_BLOCKSIZE
    logging.info(f"Reading entire FX in port {s_port.port}") # into file {filename}")

    with io.BytesIO() as binfile: # open(filename,"wb") as binfile:
        for block in range (0, blocks):
            if block & 1:
                s_port.write(b"x\xC0") #RGB BLUE OFF, buttons disabled
            else:  
                s_port.write(b"x\xC1") #RGB BLUE RED, buttons disabled
            s_port.read(1)      

            blockaddr = block * FX_BLOCKSIZE // FX_PAGESIZE

            s_port.write("A".encode())
            s_port.write(bytearray([blockaddr >> 8, blockaddr & 0xFF]))
            s_port.read(1)

            blocklen = FX_BLOCKSIZE

            s_port.write("g".encode())
            s_port.write(bytearray([(blocklen >> 8) & 0xFF, blocklen & 0xFF]))

            s_port.write("C".encode())
            contents=s_port.read(blocklen)
            binfile.write(contents)

            if report_progress:
                report_progress(block + 1, blocks)

        binfile.seek(0)
        result = binfile.read()

    s_port.write(b"x\x40")#RGB LED off, buttons enabled
    s_port.read(1)
    logging.info("Read {} blocks in {} seconds".format(blocks, round(time.time() - start,2)))

    return bytearray(result)

