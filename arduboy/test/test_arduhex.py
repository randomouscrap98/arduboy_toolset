import unittest

import arduboy.arduhex
import arduboy.image

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
    
    def test_analyze_sketch_small(self):
        bindata = makebytearray(5)
        analysis = arduboy.arduhex.analyze_sketch(bindata)
        self.assertFalse(analysis.overwrites_caterina)
        self.assertEqual(analysis.total_pages, 1)
        self.assertEqual(len(analysis.trimmed_data), 5)
        for i in range(FLASH_PAGECOUNT):
            self.assertEqual(analysis.used_pages[i], i == 0)
    
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
    
    # A transparency test is very important: although it doesn't verify the correctness of the individual
    # fields, it at least ensures reading and writing are exactly the same, and that nothing is missed
    def test_arduboy_transparency(self):
        # This is a BIG setup
        tempfile = get_tempfile_name(self._testMethodName, ".arduboy")
        parsed = arduboy.arduhex.ArduboyParsed(
            Path(tempfile).stem,
            [
                arduboy.arduhex.ArduboyBinary(
                    arduboy.arduhex.DEVICE_ARDUBOYFX,
                    "ABC123\nHELLO(THIS IS NOT HEX)",
                    makebytearray(200000),
                    makebytearray(4096)
                )
            ],
            [

            ],
            "Hecking Game",
            "0.6.8_r1",
            "yomdor",
            "It's a game about something! Press buttons and find out!",
            arduboy.image.bin_to_pilimage(makebytearray(SCREEN_BYTES)),
            "12/18/2001",
            "Action",
            "https://wow.nothing.com/hecking_game",
            "https://github.whatever/git/gitagain/git/tig/git/hecking_game",
            "no@no.com",
            "what is this supposed to be?"
        )
        arduboy.arduhex.write_arduboy(parsed, tempfile)
        parsed2 = arduboy.arduhex.read_arduboy(tempfile)

        # Apparently, because these are dataclasses, they just have a mega equality comparison anyway. Do we trust it?
        self.assertEqual(parsed, parsed2)

        # I'm wary of the hex; on the filesystem it's \r\n but here it's \n. How are they equal? Are we doing something fancy?
        self.assertEqual(parsed.binaries[0].rawhex, parsed2.binaries[0].rawhex)


if __name__ == '__main__':
    unittest.main()