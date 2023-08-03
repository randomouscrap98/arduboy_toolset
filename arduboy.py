# NOTE: a lot of this code is taken from
# https://github.com/MrBlinky/Arduboy-Python-Utilities

import constants
import logging
import time
import os
from serial.tools.list_ports  import comports
from serial import Serial
import zipfile


def get_connected_devices():
    devicelist = list(comports())
    result = []
    for device in devicelist:
        for vidpid in constants.DEVICES:
            if vidpid in device[2]:
                port=device[0]
                has_bootloader = constants.device_has_bootloader(vidpid)
                logging.debug(f"Found {device[1]} at port {port}")
                result.append({ "port": port, "has_bootloader": has_bootloader })
    return result
