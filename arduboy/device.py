# NOTE: a lot of this code is taken from
# https://github.com/MrBlinky/Arduboy-Python-Utilities

import constants
import logging
import time
import os
from dataclasses import dataclass
from serial.tools.list_ports  import comports
from serial import Serial
import zipfile

SPINSLEEP = 0.25  # Time to wait between spinning for connections
MAXRECON = 20     # Max seconds to wait for reconnection after bootloader
CONNECTWAIT = 0.1 # Why is this a thing? I don't know...

MAINBAUD = 57600

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
    
    # Disconnect the given device. Note that afterwards, information in this device
    # object is no longer valid! Might only work for arduboys (I have no idea)
    def disconnect(self):
        logging.info(f"Attempting to disonnect device {self}")
        s_port = Serial(self.port,1200)
        s_port.close()
        while self.is_connected():
            time.sleep(SPINSLEEP)
    
    # Connect to the device this represents and return the serial connection
    def connect_serial(self, baud = MAINBAUD):
        time.sleep(CONNECTWAIT)
        return Serial(self.port,baud)


# Get a list of connected Arduboy devices. Each element is an ArduboyDevice (see above)
def get_connected_devices(log = True, bootloader_only = False):
    devicelist = list(comports())
    result = []
    for device in devicelist:
        for vidpid in constants.DEVICES:
            if vidpid in device[2]:
                ardevice = ArduboyDevice(device[0], vidpid, device[1], constants.device_has_bootloader(vidpid))
                if bootloader_only and not ardevice.has_bootloader:
                    logging.debug(f"Skipping non-bootloader {ardevice}")
                    continue
                if log:
                    logging.debug(f"Found {ardevice}")
                result.append(ardevice)
    return result

# Given a connected serial port, exit the bootloader
def exit_bootloader(s_port):
   s_port.write(b"E")
   s_port.read(1)

# Find a single arduboy device, and force it to use the bootloader. Note: 
# MAY disconnect and reboot your arduboy device!
def find_single():
    devices = get_connected_devices()
    if len(devices) == 0:
        raise Exception("No Arduboys found!")
    # Assume first device is what you want
    device = devices[0]
    if not device.has_bootloader:
        device.disconnect()
        start = time.time()
        devices = get_connected_devices(log=False, bootloader_only=True)
        while len(devices) == 0:
            time.sleep(SPINSLEEP)
            if time.time() - start > MAXRECON:
                raise Exception("Could not find rebooted arduboy in time!")
            devices = get_connected_devices(log=False, bootloader_only=True)
        device = devices[0]
    return device
