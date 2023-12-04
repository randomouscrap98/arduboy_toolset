import json
import unittest
import logging

import arduboy.arduhex
import arduboy.image
import arduboy.bloggingadeadhorse

from arduboy.constants import *

from .common import *

from pathlib import Path

def get_fullcart():
    with open(TESTFULLCARTINFO_PATH, "r") as f:
        return json.loads(f.read())

class TestBloggingADeadHorse(unittest.TestCase):

    def test_prep_cartmeta_full(self):
        cartmeta = get_fullcart()
        self.assertTrue(len(cartmeta) > 100)
        result = arduboy.bloggingadeadhorse.prep_cartmeta(cartmeta, arduboy.arduhex.DEVICE_DEFAULT)
        self.assertTrue(len(result) > 100)
        for cm in result:
            self.assertTrue("image" in cm)
            self.assertEqual(len(cm["image"]), 1024)

    def test_prep_cartmeta_full_fx(self):
        cartmeta = get_fullcart()
        self.assertTrue(len(cartmeta) > 100)
        result = arduboy.bloggingadeadhorse.prep_cartmeta(cartmeta, arduboy.arduhex.DEVICE_ARDUBOYFX)
        self.assertTrue(len(result) > 100)
        for cm in result:
            self.assertTrue("image" in cm)
            self.assertEqual(len(cm["image"]), 1024)

    def test_create_csv_full(self):
        cartmeta = get_fullcart()
        prepped = arduboy.bloggingadeadhorse.prep_cartmeta(cartmeta, arduboy.arduhex.DEVICE_ARDUBOYFX)
        result = arduboy.bloggingadeadhorse.create_csv(prepped)
        self.assertTrue(len(result) > 5000)
        self.assertEqual(len(prepped) + 3, len([l for l in result.split(arduboy.bloggingadeadhorse.BADH_EOL) if l]))
    
    def test_version_greater(self):
        for (a, b) in [
            ("1.0", ""),
            ("1.0", None),
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
            (None, "1.0"),
            ("", ""),
            ("1.0", "1.0"),
            ("1.0.1_rc3", "1.0.1_rc3"),
            ]:
            self.assertFalse(arduboy.bloggingadeadhorse.version_greater(a, b)) 

    def test_empty(self):
        result = arduboy.bloggingadeadhorse.compute_update([], [], arduboy.arduhex.DEVICE_DEFAULT)
        self.assertEqual(len(result["new"]), 0)
        self.assertEqual(len(result["updates"]), 0)
        self.assertEqual(len(result["unmatched"]), 0)

    def test_full_against_empty(self):
        cartmeta = get_fullcart()
        result = arduboy.bloggingadeadhorse.compute_update([], cartmeta, arduboy.arduhex.DEVICE_DEFAULT)

        self.assertTrue(len(result["new"]) > 300) # There should be at least 300 games in the cart
        self.assertEqual(len(result["updates"]), 0)
        self.assertEqual(len(result["unmatched"]), 0)

    def test_full_against_empty_fx(self):
        cartmeta = get_fullcart()
        result = arduboy.bloggingadeadhorse.compute_update([], cartmeta, arduboy.arduhex.DEVICE_ARDUBOYFX)

        self.assertTrue(len(result["new"]) > 300) # There should be at least 300 games in the cart (even when choosing fx)
        self.assertEqual(len(result["updates"]), 0)
        self.assertEqual(len(result["unmatched"]), 0)
    
    