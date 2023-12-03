import base64
import io
import re
from typing import List
from arduboy.arduhex import DEVICE_DEFAULT
from PIL import Image

from arduboy.fxcart import TITLE_IMAGE_LENGTH, FxParsedSlot
from arduboy.image import pilimage_to_bin

CMKEY_TITLE = "title"
CMKEY_DEVELOPER = "developer"
CMKEY_IMAGE = "image"
CMKEY_CATEGORY = "info"
CMKEY_PROGRAMDATA = "pdata"
CMKEY_PROGRAM = "program"
CMKEY_VERSION = "version"
CMKEY_ID = "ID"

UPKEY_UPDATES = "updates"
UPKEY_UNMATCHED = "unmatched"
UPKEY_NEW = "new"
UPKEY_CURRENT = "current"

# I'll make a class later
# @dataclass
# class CartUpdate:
#     updates: List[(FxParsedSlot, )] = field(default_factory=lambda: [])
#     unmatched: List[FxParsedSlot] = field(default_factory=lambda: [])

def prep_cartmeta(cartmeta, device):
    result = []
    seen_ids = []

    # First, go through all the meta and pull out the right program, and also
    # create the image for the special comparison
    for cm in cartmeta:
        if cm[CMKEY_ID] in seen_ids:
            continue
        seen_ids.append(cm[CMKEY_ID])
        if device in cm[CMKEY_PROGRAM]:
            cm[CMKEY_PROGRAMDATA] = cm[CMKEY_PROGRAM][device]
        elif DEVICE_DEFAULT in cm[CMKEY_PROGRAM]:
            cm[CMKEY_PROGRAMDATA] = cm[CMKEY_PROGRAM][DEVICE_DEFAULT]
        else:
            continue

        try:
            image = base64.b64decode(cm[CMKEY_PROGRAMDATA]["image64"])
            image = Image.open(io.BytesIO(image))
            cm[CMKEY_IMAGE] = pilimage_to_bin(image)
        except:
            cm[CMKEY_IMAGE] = bytearray(TITLE_IMAGE_LENGTH)

        if CMKEY_TITLE not in cm:
            cm[CMKEY_TITLE] = ""
        if CMKEY_DEVELOPER not in cm:
            cm[CMKEY_DEVELOPER] = ""

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