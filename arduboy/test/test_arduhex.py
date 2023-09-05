import unittest
import arduboy.arduhex

from arduboy.constants import *
from .common import *

from pathlib import Path


class TestArduhex(unittest.TestCase):

    def test_read_hex(self):
        result = arduboy.arduhex.read_hex(TESTHEX_PATH)
        self.assertIsNotNone(result)
        name = Path(TESTHEX_PATH).stem
        self.assertEqual(result.original_filename, name)
        self.assertTrue(len(result.binaries) > 0, "No binaries read!")
        self.assertTrue(len(result.binaries[0].rawhex) > 20000, "Not enough data in rawhex")
        self.assertEqual(result.binaries[0].device, arduboy.arduhex.DEVICE_UNKNOWN)
        # Nothing else is guaranteed to be set
    
    def test_hex_to_bin(self):
        with open(TESTHEX_PATH, "r") as f:
            hexdata = f.read()
        bindata = arduboy.arduhex.hex_to_bin(hexdata)
        self.assertEqual(len(bindata), FLASH_SIZE)
        # We'll test other aspects of this binary using the analysis tests
    
    def test_analyze_sketch(self):
        with open(TESTHEX_PATH, "r") as f:
            hexdata = f.read()
        bindata = arduboy.arduhex.hex_to_bin(hexdata)
        analysis = arduboy.arduhex.analyze_sketch(bindata)
        self.assertFalse(analysis.overwrites_caterina)
        self.assertTrue(analysis.total_pages < FLASH_PAGECOUNT // 2)
        self.assertTrue(analysis.total_pages > FLASH_PAGECOUNT // 4)
        self.assertTrue(len(analysis.trimmed_data) < FLASH_SIZE // 2)
        self.assertTrue(len(analysis.trimmed_data) > FLASH_SIZE // 4)
    
    def test_bin_to_hex(self):
        with open(TESTHEX_PATH, "r") as f:
            hexdata = f.read()
        bindata = arduboy.arduhex.hex_to_bin(hexdata)
        analysis = arduboy.arduhex.analyze_sketch(bindata)
        newhexdata = arduboy.arduhex.bin_to_hex(analysis.trimmed_data)
        # This is funny: we're only comparing everything up to the last two lines in the original file. This works out
        # to a safety buffer of 48 characters: 13 for the last line, and UP TO 45 chars for the second to last. This may
        # not be the real size, but it's the safest amount
        complength = len(hexdata) - 48
        self.assertEqual(newhexdata[:complength], hexdata[:complength])

if __name__ == '__main__':
    unittest.main()