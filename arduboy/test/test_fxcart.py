import unittest
import arduboy.fxcart

from arduboy.constants import *
from .common import *
from pathlib import Path

class TestFxCart(unittest.TestCase):

    # This is the major test here: it's just too much effort for me to test every little function.
    # If the conversion to and from a slot is fully transparent, then I'd call that a win for now.
    # I'm aware that this doesn't ensure that data is where it needs to be; that may come later
    def test_transparent(self):
        slot = arduboy.fxcart.FxParsedSlot(
            99, 
            makebytearray(arduboy.fxcart.TITLE_IMAGE_LENGTH),
            makebytearray(9999),
            makebytearray(200000),
            makebytearray(arduboy.fxcart.SAVE_ALIGNMENT),
            arduboy.fxcart.FxSlotMeta(
                "Fun game",
                "1.0.1",
                "haloopdy",
                "Ok it's not actually that fun 😟"
            )
        )
        slotbin = arduboy.fxcart.compile_single(slot)
        newslots = arduboy.fxcart.parse(slotbin)
        self.assertTrue(len(newslots) > 0)
        slot2 = newslots[0]
        self.assertEqual(slot.category, slot2.category)
        self.assertEqual(slot.image_raw, slot2.image_raw)
        # This is because of funny padding stuff. It's not the best, and perhaps the program should be modified to not
        # change the passed in data itself
        minlen = min(len(slot.program_raw), len(slot2.program_raw))
        # Note: program has some stuff patched, skip first little section
        self.assertEqual(slot.program_raw[FLASH_PAGESIZE:minlen], slot2.program_raw[FLASH_PAGESIZE:minlen])
        self.assertEqual(slot.data_raw, slot2.data_raw[:len(slot.data_raw)])
        self.assertEqual(slot.save_raw, slot2.save_raw)
        self.assertEqual(slot.meta, slot2.meta)

if __name__ == '__main__':
    unittest.main()