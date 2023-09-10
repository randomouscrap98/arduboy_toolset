
import unittest
import arduboy.fxcart
import arduboy.arduhex
import arduboy.shortcuts
import arduboy.image

from arduboy.constants import *
from .common import *
from pathlib import Path

class TestShortcuts(unittest.TestCase):

    # This is the major test here: it's just too much effort for me to test every little function.
    # If the conversion to and from a slot is fully transparent, then I'd call that a win for now.
    # I'm aware that this doesn't ensure that data is where it needs to be; that may come later
    def test_slotfromcategory(self):
        title = "My Cat"
        info = "It's not actually a cat"
        id = 123
        image_bin = makebytearray(SCREEN_BYTES)
        result = arduboy.shortcuts.slot_from_category(title, info, arduboy.image.bin_to_pilimage(image_bin), id)
        self.assertEqual(result.meta.title, title)
        self.assertEqual(result.meta.info, info)
        self.assertEqual(result.category, id)
        self.assertEqual(image_bin, result.image_raw)
    
    def test_slotfromarduboy(self):
        ardparsed = arduboy.arduhex.ArduboyParsed(
            "notimportant",
            [],
            [],
            "MyPgoram",
            "3.9.8",
            "yeahauthor",
            "waht do you want me to say",
            "BIG LICENSE BIG IMPORATN",
            "2023/5/6",
            "action",
            "https://url",
            "https://anotherurl.jfkd",
            "email@no",
            "companion"
        )
        with open(TESTHEX_PATH, "r") as f:
            binary = arduboy.arduhex.ArduboyBinary(
                arduboy.arduhex.DEVICE_ARDUBOYFX,
                "Some Title",
                f.read(),
                makebytearray(10000),
                makebytearray(4096),
                arduboy.image.bin_to_pilimage(makebytearray(SCREEN_BYTES))
            )
        slot = arduboy.shortcuts.slot_from_arduboy(ardparsed, binary)
        self.assertEqual(slot.meta.title, ardparsed.title)
        self.assertEqual(slot.meta.info, ardparsed.description)
        self.assertEqual(slot.meta.developer, ardparsed.author)
        self.assertEqual(slot.meta.version, ardparsed.version)
        self.assertEqual(slot.category, 0)
        self.assertEqual(slot.program_raw, arduboy.common.hex_to_bin(binary.hex_raw)) # [:len(slot.program_raw)])
        self.assertEqual(slot.data_raw, binary.data_raw)
        self.assertEqual(slot.save_raw, binary.save_raw)
        self.assertEqual(slot.image_raw, arduboy.image.pilimage_to_bin(binary.cartImage))
    
    def test_slotfromarduboy_notitle(self):
        ardparsed = arduboy.arduhex.ArduboyParsed(
            "heckingfilename"
        )
        binary = arduboy.arduhex.ArduboyBinary()
        slot = arduboy.shortcuts.slot_from_arduboy(ardparsed, binary)
        self.assertEqual(slot.meta.title, ardparsed.original_filename)

    def test_arduboyfromslot_fx(self):
        slot = arduboy.fxcart.FxParsedSlot(
            99,
            makebytearray(SCREEN_BYTES),
            makebytearray(100),
            makebytearray(200000),
            makebytearray(4096),
            arduboy.fxcart.FxSlotMeta(
                "SomeTitle",
                "1.0",
                "dummy",
                "it's a dumb game"
            )
        )
        ardparsed = arduboy.shortcuts.arduboy_from_slot(slot, arduboy.arduhex.DEVICE_ARDUBOYMINI)
        self.assertEqual(ardparsed.title, slot.meta.title)
        self.assertEqual(ardparsed.description, slot.meta.info)
        self.assertEqual(ardparsed.author, slot.meta.developer)
        self.assertEqual(ardparsed.version, slot.meta.version)
        self.assertEqual(ardparsed.binaries[0].save_raw, slot.save_raw)
        self.assertEqual(ardparsed.binaries[0].data_raw, slot.data_raw)
        self.assertEqual(ardparsed.binaries[0].hex_raw, arduboy.common.bin_to_hex(slot.program_raw))
        self.assertEqual(ardparsed.binaries[0].device, arduboy.arduhex.DEVICE_ARDUBOYMINI)
        self.assertEqual(arduboy.image.pilimage_to_bin(ardparsed.binaries[0].cartImage), slot.image_raw)

    def test_arduboyfromslot_plain(self):
        slot = arduboy.fxcart.FxParsedSlot(
            99,
            makebytearray(SCREEN_BYTES),
            makebytearray(100),
            bytearray(),
            bytearray(),
            arduboy.fxcart.FxSlotMeta(
                "SomeTitle",
                "1.0",
                "dummy",
                "it's a dumb game"
            )
        )
        ardparsed = arduboy.shortcuts.arduboy_from_slot(slot, arduboy.arduhex.DEVICE_ARDUBOYMINI)
        self.assertEqual(ardparsed.title, slot.meta.title)
        self.assertEqual(ardparsed.description, slot.meta.info)
        self.assertEqual(ardparsed.author, slot.meta.developer)
        self.assertEqual(ardparsed.version, slot.meta.version)
        self.assertTrue(ardparsed.binaries[0].save_raw is None or len(ardparsed.binaries[0].save_raw) == 0, "Save was present when not supposed to be")
        self.assertTrue(ardparsed.binaries[0].data_raw is None or len(ardparsed.binaries[0].data_raw) == 0, "Data was present when not supposed to be")
        self.assertEqual(ardparsed.binaries[0].hex_raw, arduboy.common.bin_to_hex(slot.program_raw))
        # THE IMPORTANT TEST: Even though we passed ARduboyMini, it should've picked ARduboy because no fx data
        self.assertEqual(ardparsed.binaries[0].device, arduboy.arduhex.DEVICE_ARDUBOY)
        self.assertEqual(arduboy.image.pilimage_to_bin(ardparsed.binaries[0].cartImage), slot.image_raw)

if __name__ == '__main__':
    unittest.main()