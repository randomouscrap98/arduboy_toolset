import unittest
from arduboy.common import *
from arduboy.constants import *

class TestCommon(unittest.TestCase):

    def test_pad_data_exact(self):
        data = bytearray([1,2,3,4,5])
        result = pad_data(data, 5)
        self.assertEqual(data, result)

    def test_pad_data_multiple(self):
        data = bytearray([1,2,3,4,5,6])
        result = pad_data(data, 3)
        self.assertEqual(data, result)

    def test_pad_data_smaller(self):
        data = bytearray([1,2,3,4,5])
        expected = bytearray([1,2,3,4,5,0xFF])
        result = pad_data(data, 3)
        self.assertEqual(expected, result)

    def test_pad_data_larger(self):
        data = bytearray([1,2,3,4,5])
        expected = bytearray([1,2,3,4,5,0xFF,0xFF])
        result = pad_data(data, 7)
        self.assertEqual(expected, result)

    def test_pad_data_special(self):
        data = bytearray([1,2,3,4,5,6,7,8,9])
        expected = bytearray([1,2,3,4,5,6,7,8,9,69,69,69])
        result = pad_data(data, 4, int.to_bytes(69, 1, 'little'))
        self.assertEqual(expected, result)
    
    def test_padsize(self):
        tests = [
            (5, 5, 0),
            (5, 6, 1),
            (5, 3, 1),
            (9, 4, 3),
        ]
        for length, align, expected in tests:
            with self.subTest(length = length, align = align, expected = expected):
                self.assertEqual(pad_size(length, align), expected)

    def test_bytebit(self):
        tests = [
            (0b11001010, 0, 0),
            (0b11001010, 1, 1),
            (0b11001010, 2, 0),
            (0b11001010, 3, 1),
            (0b11001010, 4, 0),
            (0b11001010, 5, 0),
            (0b11001010, 6, 1),
            (0b11001010, 7, 1),
        ]
        for num, pos, expected in tests:
            with self.subTest(num = num, pos = pos, expected = expected):
                self.assertEqual(bytebit(num, pos), expected)

    def test_int_to_hex(self):
        tests = [
            (5, 1, "5"),
            (5, 2, "05"),
            (5, 4, "0005"),
            (15, 1, "F"),
            (15, 2, "0F"),
            (255, 2, "FF"),
            (255, 4, "00FF")
        ]
        for i, len, expected in tests:
            with self.subTest(i = i, len = len, expected = expected):
                self.assertEqual(int_to_hex(i, len), expected)

    def test_count_unused_pages_small(self):
        data = bytearray([1,2,3,4,5])
        self.assertEqual(0, count_unused_pages(data))

    def test_count_unused_pages_noalignment(self):
        data = bytearray([1,2,3,4,5])
        data += b'\xFF' * FX_PAGESIZE
        self.assertEqual(1, count_unused_pages(data))

    def test_count_unused_pages_off_by_1_nopage(self):
        data = bytearray([1,2,3,4,5])
        data += b'\xFF' * (FX_PAGESIZE - 1)
        self.assertEqual(0, count_unused_pages(data))

    def test_count_unused_pages_off_by_1_withpage(self):
        data = bytearray([1,2,3,4,5])
        data += b'\xFF' * (FX_PAGESIZE * 2 - 1)
        self.assertEqual(1, count_unused_pages(data))

    def test_count_unused_pages_off_by_1_overpage(self):
        data = bytearray([1,2,3,4,5])
        data += b'\xFF' * (FX_PAGESIZE * 2 + 1)
        self.assertEqual(2, count_unused_pages(data))

if __name__ == '__main__':
    unittest.main()