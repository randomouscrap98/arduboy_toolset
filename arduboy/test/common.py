import os
import time

from io import BytesIO

# Assumes running from root (careful!)
TESTFILES_DIR = "testfiles"
JUNKFILES_DIR = os.path.join(TESTFILES_DIR,"ignore")

TESTHEX_FILENAME = "pong.hex"
TESTHEX_PATH = os.path.join(TESTFILES_DIR, TESTHEX_FILENAME)

TESTHEXFX_FILENAME = "mmfx.hex"
TESTHEXFX_PATH = os.path.join(TESTFILES_DIR, TESTHEXFX_FILENAME)

TESTARDUBOYV2_FILENAME = "mc.arduboy"
TESTARDUBOYV2_PATH = os.path.join(TESTFILES_DIR, TESTARDUBOYV2_FILENAME)

TESTARDUBOYV3_FILENAME = "mmfx.arduboy"
TESTARDUBOYV3_PATH = os.path.join(TESTFILES_DIR, TESTARDUBOYV3_FILENAME)

def get_filesafe_datetime():
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())

def makebytearray(length: int) -> bytearray:
    buffer = BytesIO()
    for i in range(length):
        buffer.write(int.to_bytes(i & 0xFF, 1, 'little')) # [i & 0xFF])
    return bytearray(buffer.getvalue())

def get_tempfile_name(testname, extension: str) -> str:
    os.makedirs(JUNKFILES_DIR, exist_ok=True)
    return os.path.join(JUNKFILES_DIR, f"{testname}_{get_filesafe_datetime()}_{extension}")