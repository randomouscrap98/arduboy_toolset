# NOTE: a lot of this code is taken from
# https://github.com/MrBlinky/Arduboy-Python-Utilities

import zipfile
import tempfile
import os
import logging

# Read so-called "records" from the given arduboy file. No parsing or verification is done yet.
def read_arduboy(filepath):
    try:
        # First, we try to open the file as a zip. This apparently handles both .zip and .arduboy
        # files; this is how Mr.Blink's arduboy python utilities works (mostly)
        with zipfile.ZipFile(filepath) as zip_ref:
            logging.debug(f"Input file {filepath} is zip archive, scanning for hex file")
            for filename in zip_ref.namelist():
                if filename.lower().endswith(".hex"):
                    # Create a temporary directory to hold the file (and other contents maybe later)
                    with tempfile.TemporaryDirectory() as temp_dir:
                        zip_ref.extract(filename, temp_dir)
                        extract_file = os.path.join(temp_dir, filename)
                        # The arduboy utilities opens with just "r", no binary flags set.
                        logging.debug(f"Reading hex file {extract_file} (taken from archive into temp file, validating later)")
                        with open(extract_file,"r") as f:
                            return f.readlines()
    except:
        logging.debug(f"Reading potential hex file {filepath} (validating later)")
        with open(filepath,"r") as f:
            return f.readlines()
