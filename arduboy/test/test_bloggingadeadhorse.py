import json
import unittest
import logging

import arduboy.arduhex
import arduboy.image
import arduboy.bloggingadeadhorse

from arduboy.constants import *

from .common import *

from pathlib import Path


class TestBloggingADeadHorse(unittest.TestCase):

    def test_empty(self):
        result = arduboy.bloggingadeadhorse.compute_update([], [], arduboy.arduhex.DEVICE_DEFAULT)
        self.assertEqual(len(result["new"]), 0)
        self.assertEqual(len(result["updates"]), 0)
        self.assertEqual(len(result["unmatched"]), 0)
    
    def test_prep_cartmeta_full(self):
        with open(TESTFULLCARTINFO_PATH, "r") as f:
            cartmeta = json.loads(f.read())
        self.assertTrue(len(cartmeta) > 100)
        result = arduboy.bloggingadeadhorse.prep_cartmeta(cartmeta, arduboy.arduhex.DEVICE_DEFAULT)
        self.assertTrue(len(result) > 100)
        for cm in result:
            self.assertTrue("image" in cm)
            self.assertEqual(len(cm["image"]), 1024)
    
    def test_version_greater(self):
        for (a, b) in [
            ("1.0", ""),
            ("1.0", "0.1"),
            ("1.0", "1"),
            ("2.0", "1.0"),
            ("2.0.1", "2.0.0"),
            ("2.0.0.1", "2.0.0.0"),
            ("2.1", "2.0.9.9"),
            ("2.1_rc1", "2.1.0")
            ]:
            self.assertTrue(arduboy.bloggingadeadhorse.version_greater(a, b)) 
        for (a, b) in [
            ("", ""),
            ("1.0", "1.0"),
            ("1.0.1_rc3", "1.0.1_rc3"),
            ]:
            self.assertFalse(arduboy.bloggingadeadhorse.version_greater(a, b)) 
