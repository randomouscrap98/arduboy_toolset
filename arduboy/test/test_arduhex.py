import unittest
import logging

# try:
import arduboy.arduhex
import arduboy.image
from arduboy.constants import *
# except:
#     import arduboy.arduhex
#     import arduboy.image
#     from arduboy.constants import *

from .common import *

from pathlib import Path


class TestArduhex(unittest.TestCase):

    def test_device_allowed(self):
        self.assertTrue(arduboy.arduhex.device_allowed(arduboy.arduhex.DEVICE_ARDUBOY, arduboy.arduhex.DEVICE_ARDUBOY))
        self.assertTrue(arduboy.arduhex.device_allowed(arduboy.arduhex.DEVICE_ARDUBOYFX, arduboy.arduhex.DEVICE_ARDUBOY))
        self.assertTrue(arduboy.arduhex.device_allowed(arduboy.arduhex.DEVICE_ARDUBOYMINI, arduboy.arduhex.DEVICE_ARDUBOY))
        self.assertFalse(arduboy.arduhex.device_allowed(arduboy.arduhex.DEVICE_ARDUBOY, arduboy.arduhex.DEVICE_ARDUBOYFX))
        self.assertFalse(arduboy.arduhex.device_allowed(arduboy.arduhex.DEVICE_ARDUBOY, arduboy.arduhex.DEVICE_ARDUBOYMINI))
        self.assertFalse(arduboy.arduhex.device_allowed(arduboy.arduhex.DEVICE_ARDUBOYMINI, arduboy.arduhex.DEVICE_ARDUBOYFX))
        self.assertFalse(arduboy.arduhex.device_allowed(arduboy.arduhex.DEVICE_ARDUBOYFX, arduboy.arduhex.DEVICE_ARDUBOYMINI))
    
    def test_empty_arduhex(self):
        empty = arduboy.arduhex.empty_parsed_arduboy()
        self.assertEqual(len(empty.binaries), 0)
        self.assertEqual(len(empty.contributors), 0)

    def test_read_hex(self):
        result = arduboy.arduhex.read_hex(TESTHEX_PATH)
        self.assertIsNotNone(result)
        name = Path(TESTHEX_PATH).stem
        self.assertEqual(result.original_filename, name)
        self.assertTrue(len(result.binaries) > 0, "No binaries read!")
        self.assertTrue(len(result.binaries[0].hex_raw) > 20000, "Not enough data in hex_raw")
        self.assertEqual(result.binaries[0].device, arduboy.arduhex.DEVICE_DEFAULT)
        # Nothing else is guaranteed to be set
    
    def test_read_arduboy_v2(self):
        # Even with V2 must be able to read them
        result = arduboy.arduhex.read_arduboy(TESTARDUBOYV2_PATH)
        self.assertIsNotNone(result)
        name = Path(TESTARDUBOYV2_PATH).stem
        self.assertEqual(result.original_filename, name)
        self.assertTrue(len(result.binaries) > 0, "No binaries read!")
        self.assertTrue(len(result.binaries[0].hex_raw) > 40000, "Not enough data in hex_raw")
        self.assertEqual(len(result.binaries[0].data_raw), 0, "Should not be any data!")
        self.assertEqual(len(result.binaries[0].save_raw), 0, "Should not be any save data!")
        self.assertEqual(result.binaries[0].device, arduboy.arduhex.DEVICE_ARDUBOY)
        self.assertEqual(result.title, "MicroCity")
        self.assertEqual(result.author, "James Howard")
        self.assertEqual(result.version, "1.1")
        self.assertEqual(result.date, "2018-02-22")
        self.assertEqual(result.genre, "Misc")

    def test_read_arduboy_old_contributors(self):
        # Based on our modified v2, we should also test the field merging.
        result = arduboy.arduhex.read_arduboy(TESTARDUBOYV2_PATH)
        self.assertEqual(len(result.contributors), 3)
        for c in result.contributors:
            self.assertEqual(len(c.urls), 0)
            if c.name == "User1":
                self.assertTrue("Publisher" in c.roles)
                self.assertTrue("Code" in c.roles)
            elif c.name == "User2":
                self.assertTrue("Idea" in c.roles)
            elif c.name == "User3":
                self.assertTrue("Sound" in c.roles)
                self.assertTrue("Art" in c.roles)
            else:
                raise Exception("Unknown contributor: " + c.name)
    
    def test_read_arduboy_v3_blankcontributors(self):
        result = arduboy.arduhex.read_arduboy(TESTARDUBOYV3_PATH)
        self.assertEqual(len(result.contributors), 0)

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
        self.assertEqual(analysis.detected_device, arduboy.arduhex.DEVICE_ARDUBOY)
    
    def test_analyze_sketch_fx(self):
        with open(TESTHEXFX_PATH, "r") as f:
            hexdata = f.read()
        bindata = arduboy.common.hex_to_bin(hexdata)
        analysis = arduboy.arduhex.analyze_sketch(bindata)
        self.assertFalse(analysis.overwrites_caterina)
        self.assertTrue(analysis.total_pages > FLASH_PAGECOUNT // 2)
        self.assertTrue(analysis.total_pages < FLASH_PAGECOUNT)
        self.assertTrue(len(analysis.trimmed_data) > FLASH_SIZE // 2)
        self.assertTrue(len(analysis.trimmed_data) < FLASH_SIZE)
        self.assertEqual(analysis.detected_device, arduboy.arduhex.DEVICE_ARDUBOYFX)
    
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
                    "The title of the binary",
                    "ABC123\nHELLO(THIS IS NOT HEX)",
                    makebytearray(200000),
                    makebytearray(4096),
                    arduboy.image.bin_to_pilimage(makebytearray(SCREEN_BYTES)),
                ),
                arduboy.arduhex.ArduboyBinary(
                    arduboy.arduhex.DEVICE_ARDUBOY,
                    "REQUIRED", # If you leave the title out, transparency is ruined. A title is auto-assigned on write
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
            "BIG LICENSE BIG IMPORTANT",
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

    def test_writearduboy_autotitle(self):
        tempfile = get_tempfile_name(self._testMethodName, ".arduboy")
        parsed = arduboy.arduhex.ArduboyParsed(
            Path(tempfile).stem,
            [
                arduboy.arduhex.ArduboyBinary(
                    arduboy.arduhex.DEVICE_ARDUBOYFX,
                    "",
                    "ABC123\nHELLO(THIS IS NOT HEX)"
                ),
            ],
            [ ],
            "Hecking Game",
        )
        arduboy.arduhex.write_arduboy(parsed, tempfile)
        parsed2 = arduboy.arduhex.read_arduboy(tempfile)
        self.assertTrue(parsed.title in parsed2.binaries[0].title)
        self.assertTrue(parsed.binaries[0].device in parsed2.binaries[0].title)

    def test_writearduboy_noautotitle(self):
        tempfile = get_tempfile_name(self._testMethodName, ".arduboy")
        parsed = arduboy.arduhex.ArduboyParsed(
            Path(tempfile).stem,
            [
                arduboy.arduhex.ArduboyBinary(
                    arduboy.arduhex.DEVICE_ARDUBOYFX,
                    "SOMEGARBO",
                    "ABC123\nHELLO(THIS IS NOT HEX)"
                ),
            ],
            [ ],
            "Hecking Game",
        )
        arduboy.arduhex.write_arduboy(parsed, tempfile)
        parsed2 = arduboy.arduhex.read_arduboy(tempfile)
        self.assertFalse(parsed.title in parsed2.binaries[0].title)
        self.assertFalse(parsed.binaries[0].device in parsed2.binaries[0].title)

        
if __name__ == '__main__':
    unittest.main()