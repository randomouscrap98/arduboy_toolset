from arduboy.arduhex import DEVICE_DEFAULT

import base64
import io
import re
import logging
import json

from typing import List
from PIL import Image

from arduboy.fxcart import TITLE_IMAGE_LENGTH, FxParsedSlot
from arduboy.image import pilimage_to_bin

CMKEY_TITLE = "title"
CMKEY_DEVELOPER = "developer"
CMKEY_INFO = "info"
CMKEY_CATEGORY = "info" # TODO: wait for Filmote to update this
CMKEY_PROGRAMDATA = "pdata"
CMKEY_PROGRAM = "program"
CMKEY_VERSION = "version"
CMKEY_ID = "ID"

CMKEY_IMAGE = "image"
CMKEY_HEX = "hex"
CMKEY_FXDATA = "fxdata"
CMKEY_FXSAVE = "fxsave"

UPKEY_UPDATES = "updates"
UPKEY_UNMATCHED = "unmatched"
UPKEY_NEW = "new"
UPKEY_CURRENT = "current"

BADH_EOL = "<eol/>"

# I'll make a class later
# @dataclass
# class CartUpdate:
#     updates: List[(FxParsedSlot, )] = field(default_factory=lambda: [])
#     unmatched: List[FxParsedSlot] = field(default_factory=lambda: [])

class CartMetaDecoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytearray) or isinstance(obj, FxParsedSlot):
            # Convert bytearray to a list of integers
            return False
        return super().default(obj)


# Must already be prepped!
def create_csv(cartmeta):
    # Make some fake data, we aren't actually going to use this stuff
    output = 'List;Description;Title;Hex;Data;Save;Version;Developer;Info;Likes;URL;Source;Start;End;Hash' + BADH_EOL
    output += '0;Bootloader;arduboy-fx-loader.png;;;;;;;;;;;;<eol/>'
    # JUST IN CASE, make a fake category so everyone is happy
    output += '1;FAKE_CATEGORY;category-screens/Action.png;;;;;;;;;;;;<eol/>'
    # And now we actually start adding all the little bits and pieces.
    id = 2

    # Realistically, we should use a csv builder for this, but I'm worried about any funny quirks the website has,
    # so I'm just doing it almost exactly like it's done on the website
    for cm in cartmeta:
        output += f"{id};{cm[CMKEY_TITLE]};{getpd(cm,CMKEY_IMAGE)};{getpd(cm,CMKEY_HEX)};{getpd(cm,CMKEY_FXDATA)};{getpd(cm,CMKEY_FXSAVE)};"
        info = cm[CMKEY_INFO].replace(";", ",") # Just in case (the website doesn't do this!)
        output += f"{cm[CMKEY_VERSION]};{cm[CMKEY_DEVELOPER]};{info};;;;;;;{BADH_EOL}"
        # NOTE: in the above, there are 7 semicolons. This is technically incorrect, but it's how the website works, so we've 
        # added that extra one (there should only be 6)
        id += 1

    return output

def getpd(cm, key):
    return cm[CMKEY_PROGRAMDATA].get(key, '')


def prep_cartmeta(cartmeta, device):
    result = []
    seen_ids = []

    # First, go through all the meta and pull out the right program, and also
    # create the image for the special comparison
    for cm in cartmeta:
        if cm[CMKEY_ID] in seen_ids:
            continue
        # Completely ignore metadata that doesn't include important data
        if CMKEY_TITLE not in cm or CMKEY_DEVELOPER not in cm or CMKEY_VERSION not in cm:
            continue

        seen_ids.append(cm[CMKEY_ID])
        if device in cm[CMKEY_PROGRAM]:
            cm[CMKEY_PROGRAMDATA] = cm[CMKEY_PROGRAM][device]
        elif DEVICE_DEFAULT in cm[CMKEY_PROGRAM]:
            cm[CMKEY_PROGRAMDATA] = cm[CMKEY_PROGRAM][DEVICE_DEFAULT]
        else:
            continue

        image_raw = None 

        try:
            image_raw = base64.b64decode(cm[CMKEY_PROGRAMDATA]["image64"])
            image = Image.open(io.BytesIO(image_raw))
            cm[CMKEY_IMAGE] = pilimage_to_bin(image)
        except Exception as ex:
            logging.error(f"Couldn't decode image64 from badh game '{cm[CMKEY_TITLE]}'[{cm[CMKEY_ID]}]: {ex}")
            cm[CMKEY_IMAGE] = bytearray(TITLE_IMAGE_LENGTH)
            if image_raw:
                with open(f'{cm[CMKEY_ID]}.png', "wb") as f:
                    f.write(image_raw)

        # if CMKEY_TITLE not in cm:
        #     cm[CMKEY_TITLE] = ""
        # if CMKEY_DEVELOPER not in cm:
        #     cm[CMKEY_DEVELOPER] = ""

        result.append(cm)
    
    return result


def parse_version(v):
    if v is None:
        v = ""
    dv = re.findall(r'\d+', v)
    return [int(d) for d in dv]


def version_greater(a, b):
    """Return true if a > b"""
    da = parse_version(a)
    db = parse_version(b)

    for i in range(min(len(da), len(db))):
        if da[i] > db[i]:
            return True
        elif da[i] < db[i]:
            return False

    # If all positions possible are the same, version a is greater if it has more segments
    return len(da) > len(db)


def compute_update(originalcart: List[FxParsedSlot], cartmeta, device):
    """
    Given a cart and the cartmeta from the website, try hard to compute the updates
    and new things
    """

    unmatched = originalcart.copy()
    validmeta = prep_cartmeta(cartmeta, device)
    updates = []
    current = []

    # First, do the "fast" check, this will hopefully get a lot of the possibilities out. 
    # We're just looking for updates where the title + developer match, but the version
    # on the server is newer
    for item in unmatched.copy():
        for cm in validmeta:
            if item.meta.title and item.meta.title.lower() == cm[CMKEY_TITLE].lower():
                if item.meta.developer and item.meta.developer.lower() == cm[CMKEY_DEVELOPER].lower():
                    if version_greater(cm[CMKEY_VERSION], item.meta.version):
                        updates.append((item, cm))
                    else:
                        current.append((item, cm))
                    validmeta.remove(cm)
                    unmatched.remove(item)
                    break
    
    # Now for anything remaining, we want to match by exact title screen. THis might be slow?
    for item in unmatched.copy():
        for cm in validmeta:
            if item.image_raw == cm[CMKEY_IMAGE]:
                if version_greater(cm[CMKEY_VERSION], item.meta.version):
                    updates.append((item, cm))
                else: 
                    current.append((item, cm))
                validmeta.remove(cm)
                unmatched.remove(item)
                break

    return {
        UPKEY_UNMATCHED : unmatched,
        UPKEY_UPDATES : updates,
        UPKEY_NEW : validmeta,
        UPKEY_CURRENT : current
    }