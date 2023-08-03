# NOTE: a lot of this code is taken from
# https://github.com/MrBlinky/Arduboy-Python-Utilities

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

LCDBOOTPROGRAM = b"\xD5\xF0\x8D\x14\xA1\xC8\x81\xCF\xD9\xF1\xAF\x20\x00"


def device_has_bootloader(vpid):
    return (DEVICES.index(vpid) & 1) == 0
