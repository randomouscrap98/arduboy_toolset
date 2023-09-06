import unittest
import logging

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
        self.assertTrue(len(result.binaries[0].hex_raw) > 20000, "Not enough data in hex_raw")
        self.assertEqual(result.binaries[0].device, arduboy.arduhex.DEVICE_DEFAULT)
        # Nothing else is guaranteed to be set
    
    def test_read_arduboy_v3(self):
        # Even with V3 must be able to read them
        result = arduboy.arduhex.read_arduboy(TESTARDUBOYV3_PATH)
        self.assertIsNotNone(result)
        name = Path(TESTARDUBOYV3_PATH).stem
        self.assertEqual(result.original_filename, name)
        self.assertTrue(len(result.binaries) > 0, "No binaries read!")
        self.assertTrue(len(result.binaries[0].hex_raw) > 40000, "Not enough data in hex_raw")
        self.assertTrue(len(result.binaries[0].data_raw) > 15000, "Not enough data in data_raw")
        self.assertEqual(len(result.binaries[0].save_raw), 0, "Should not be any save data!")
        self.assertEqual(result.binaries[0].device, arduboy.arduhex.DEVICE_ARDUBOYFX)
        self.assertEqual(result.title, "Manic Miner FX")
        self.assertEqual(result.author, "marggines - smBIT")
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.date, "2023-03-11")
        self.assertEqual(result.genre, "platform")
    
    def test_analyze_sketch(self):
        with open(TESTHEX_PATH, "r") as f:
            hexdata = f.read()
        bindata = arduboy.common.hex_to_bin(hexdata)
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
                    makebytearray(4096),
                    arduboy.image.bin_to_pilimage(makebytearray(SCREEN_BYTES)),
                ),
                arduboy.arduhex.ArduboyBinary(
                    arduboy.arduhex.DEVICE_ARDUBOY,
                    "MORE NOT HEX LOL"
                )
            ],
            [
                arduboy.arduhex.ArduboyContributor("Firstname Lastname", ["Coding", "Coder"]),
                arduboy.arduhex.ArduboyContributor("Nobody"),
                arduboy.arduhex.ArduboyContributor("Artistman", ["Art"], ["https://place.com", "https://art.com"]),
            ],
            "Hecking Game",
            "0.6.8_r1",
            "yomdor",
            "It's a game about something! Press buttons and find out!",
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


if __name__ == '__main__':
    unittest.main()