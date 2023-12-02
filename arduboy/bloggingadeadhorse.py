import base64
import io
import re
from typing import List
from arduboy.arduhex import DEVICE_DEFAULT
from PIL import Image

from arduboy.fxcart import FxParsedSlot
from arduboy.image import pilimage_to_bin

# I'll make a class later
# @dataclass
# class CartUpdate:
#     updates: List[(FxParsedSlot, )] = field(default_factory=lambda: [])
#     unmatched: List[FxParsedSlot] = field(default_factory=lambda: [])

def prep_cartmeta(cartmeta, device):
    result = []

    # First, go through all the meta and pull out the right program, and also
    # create the image for the special comparison
    for cm in cartmeta:
        if device in cm["program"]:
            cm["pdata"] = cm["program"][device]
        elif DEVICE_DEFAULT in cm["program"]:
            cm["pdata"] = cm["program"][device]
        else:
            continue

        image = base64.b64decode(cm["pdata"]["image64"])
        image = Image.open(io.BytesIO(image))
        cm["image"] = pilimage_to_bin(image)
        cm["category"] = cm["info"] # website calls it "info", but I'm calling it category

        result.append(cm)
    
    return result

def parse_version(v):
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

    result = {
        "unmatched" : originalcart.copy(),
        "updates" : []
    }

    validmeta = prep_cartmeta(cartmeta, device)


    result["new"] = validmeta

    return result