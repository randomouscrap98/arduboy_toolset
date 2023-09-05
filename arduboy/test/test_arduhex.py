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
    
    def test_read_arduboy(self):
        pass

if __name__ == '__main__':
    unittest.main()