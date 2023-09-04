import unittest
from arduboy.common import *

class TestCommon(unittest.TestCase):

    def test_pad_data_exact(self):
        data = bytearray([1,2,3,4,5])
        result = pad_data(data, 5)
        self.assertEqual(data, result)

    def test_pad_data_smaller(self):
        data = bytearray([1,2,3,4,5])
        expected = bytearray([1,2,3,4,5,0xFF])
        result = pad_data(data, 3)
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()