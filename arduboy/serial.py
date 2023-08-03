# Given a connected serial port, exit the bootloader
import logging


def exit_bootloader(s_port):
   s_port.write(b"E")
   s_port.read(1)

# Given a connected serial port, see if bootloader is "caterina"
def is_caterina(s_port):
    s_port.write(b"V") #get bootloader software version
    if s_port.read(2) == b"10" : #original caterina 1.0 bootloader
        s_port.write(b"r") #read lock bits
        return ord(s_port.read(1)) & 0x10 != 0
    return False

# Flash the given arduboy hex file to the given connected arduboy. Can report progress
# by giving a function that accepts a "current" and "total" parameter.
def flash_arduhex(arduhex, s_port, report_progress: None):
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
                raise Exception("\nVerify failed at address {:04X}. Upload unsuccessful.".format(i * 128))
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

