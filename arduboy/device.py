# NOTE: a lot of this code is taken from
# https://github.com/MrBlinky/Arduboy-Python-Utilities

import logging
import time
from dataclasses import dataclass
from serial.tools.list_ports  import comports
from serial import Serial

FLASHSIZE = 32768         # Size of the onboard flash (default chip whatever, atmega etc)
FXPAGESIZE = 256
FXBLOCKSIZE = 65536
FXPAGES_PER_BLOCK = FXBLOCKSIZE // FXPAGESIZE
FXMAX_PAGES = 65536     # This times page size is 16MB, as expected

DEVICES = [
    #Arduboy Leonardo
    "VID:PID=2341:0036", "VID:PID=2341:8036",
    "VID:PID=2A03:0036", "VID:PID=2A03:8036",
    #Arduboy Micro
    "VID:PID=2341:0037", "VID:PID=2341:8037",
    "VID:PID=2A03:0037", "VID:PID=2A03:8037",
    #Genuino Micro
    "VID:PID=2341:0237", "VID:PID=2341:8237",
    #Sparkfun Pro Micro 5V
    "VID:PID=1B4F:9205", "VID:PID=1B4F:9206",
    #Adafruit ItsyBitsy 5V
    "VID:PID=239A:000E", "VID:PID=239A:800E",
]

MANUFACTURERS = {
  0x01 : "Spansion",
  0x14 : "Cypress",
  0x1C : "EON",
  0x1F : "Adesto(Atmel)",
  0x20 : "Micron",
  0x37 : "AMIC",
  0x9D : "ISSI",
  0xC2 : "General Plus",
  0xC8 : "Giga Device",
  0xBF : "Microchip",
  0xEF : "Winbond"
}

SPINSLEEP = 0.25  # Time to wait between spinning for connections
MAXRECON = 20     # Max seconds to wait for reconnection after bootloader
CONNECTWAIT = 0.1 # Why is this a thing? I don't know...
MAINBAUD = 57600

def device_has_bootloader(vidpid):
    return (DEVICES.index(vidpid) & 1) == 0

# Represents a connected arduboy device. May NOT still be connected, simply
# information at the time of reading!
@dataclass
class ArduboyDevice:
    port: str
    vidpid: str
    name: str
    has_bootloader: bool

    # Display self as string (show pertinent information)
    def __str__(self):
        result = f"{self.vidpid}({self.port})"
        if self.has_bootloader:
            result += "[bootld]"
        return result

    # Determine whether if, at this very moment, this device is connected
    def is_connected(self):
        devices = get_connected_devices(log = False)
        return any(x.port == self.port and x.vidpid == self.vidpid for x in devices)
    
    # Connect to the device this represents and return the serial connection
    def connect_serial(self, baud = MAINBAUD):
        time.sleep(CONNECTWAIT)
        return Serial(self.port,baud)


# Get a list of connected Arduboy devices. Each element is an ArduboyDevice (see above)
def get_connected_devices(log = True, bootloader_only = False):
    devicelist = list(comports())
    result = []
    for device in devicelist:
        for vidpid in DEVICES:
            if vidpid in device[2]:
                ardevice = ArduboyDevice(device[0], vidpid, device[1], device_has_bootloader(vidpid))
                if bootloader_only and not ardevice.has_bootloader:
                    logging.debug(f"Skipping non-bootloader {ardevice}")
                    continue
                if log:
                    logging.debug(f"Found {ardevice}")
                result.append(ardevice)
    return result

# Find a single arduboy device, and force it to use the bootloader. Note: 
# MAY disconnect and reboot your arduboy device!
def find_single():
    devices = get_connected_devices()
    if len(devices) == 0:
        raise Exception("No Arduboys found!")
    # Assume first device is what you want
    device = devices[0]
    if not device.has_bootloader:
        logging.info(f"Attempting to reset device {device}")
        s_port = Serial(device.port,1200)
        s_port.close()
        while device.is_connected():
            time.sleep(SPINSLEEP)
        start = time.time()
        devices = get_connected_devices(log=False, bootloader_only=True)
        while len(devices) == 0:
            time.sleep(SPINSLEEP)
            if time.time() - start > MAXRECON:
                raise Exception("Could not find rebooted arduboy in time!")
            devices = get_connected_devices(log=False, bootloader_only=True)
        device = devices[0]
    return device
