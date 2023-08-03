# NOTE: a lot of this code is taken from
# https://github.com/MrBlinky/Arduboy-Python-Utilities

import constants
import logging
import time
import os
from serial.tools.list_ports  import comports
from serial import Serial
import zipfile

DCSLEEP = 0.5

# Get a list of connected Arduboy devices. Each element in the list describes the port, whether it
# has a bootloader (has_bootloader), and the vidpid
def get_connected_devices(log = True):
    devicelist = list(comports())
    result = []
    for device in devicelist:
        for vidpid in constants.DEVICES:
            if vidpid in device[2]:
                port=device[0]
                has_bootloader = constants.device_has_bootloader(vidpid)
                if log:
                    logging.debug(f"Found {device[1]} at port {port}")
                result.append({ "port": port, "has_bootloader": has_bootloader, "vidpid": vidpid })
    return result

# Return whether a device is connected or not. Does NOT print any logging information
def device_connected(device):
    devices = get_connected_devices(log = False)
    return any(x["port"] == device["port"] and x["vidpid"] == device["vidpid"] for x in devices)

# Disconnect the device. Might only work for arduboys (I have no idea how this works!)
def disconnect_device(device):
    device = Serial(device["port"],1200)
    device.close()
    while device_connected(device):
        time.sleep(DCSLEEP)

# Given a connected serial port, exit the bootloader
def exit_bootloader(s_port):
   s_port.write(b"E")
   s_port.read(1)

# Attempt to connect to the given device (assumed to be in the format found in get_connected_devices)
# and force the bootloader. Returns the new device
# def connect_with_bootloader(device):
#     if not device["has_bootloader"]:
#         disconnect_device(device["port"])
# 
#     return device
