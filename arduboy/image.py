from arduboy.constants import *

import slugify
import io

from PIL import Image
from dataclasses import dataclass, field

# Should probably not be a constant... some kind of config?
IMAGE_THRESHOLD = 64
ALPHA_THRESHOLD = 128

# Convert a block of arduboy image bytes (should be 1024) to a PILlow image
def bin_to_pilimage(byteData, raw = False):
    byteLength = len(byteData)
    if byteLength != SCREEN_BYTES:
        raise Exception(f"Image binary not right size! Expected {SCREEN_BYTES} got {byteLength}")

    pixels = bytearray(SCREEN_WIDTH * SCREEN_HEIGHT)
    for b in range(0, len(pixels)):
        ob = b >> 3
        pixels[((((ob >> 7) << 3)+(b & 7)) << 7) + (ob & 127)] = 255 * ((byteData[ob] >> (b & 7)) & 1)
    
    if raw:
        return pixels

    img = Image.frombytes("L", (SCREEN_WIDTH, SCREEN_HEIGHT), pixels)

    return img

# Convert any PIL image with any dimensions into an arduboy binary image. Note: this means
# it could be stretched and dithered and whatever.
# Taken almost directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/flashcart-builder.py
def pilimage_to_bin(image: Image):
    binimg = convert_titlescreen(image)
    width, height  = binimg.size
    pixels = list(binimg.getdata())
    bytes = bytearray(int((height // 8) * width))
    i = 0
    b = 0
    for y in range (0,height,8):
        for x in range (0,width):
            for p in range (0,8):
                b = b >> 1  
                if pixels[(y + p) * width + x] > 0:
                    b |= 0x80
            bytes[i] = b
            i += 1
    return bytes
    

# Try to get the given image in the right format and size for Arduboy. Still returns a PIL image.
def convert_titlescreen(image):
    width, height = image.size
    # Actually for now I'm just gonna stretch it, I don't care! Hahaha TODO: fix this
    if width != SCREEN_WIDTH or height != SCREEN_HEIGHT:
        image = image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.NEAREST)
    image = image.convert("1") # Do this after because it's probably better AFTER nearest neighbor
    return image


# Determine if image has transparency. Can pass raw pixels (must be list created from getdata)
def has_transparency(image):
    if isinstance(image, Image.Image):
        pixels = list(image.convert("RGBA").getdata())
    else:
        pixels = image
    for i in pixels:
        if i[3] < 255:
            return True
    return False


@dataclass
class TileConfig:
    width: int = field(default=0)           # Width of tile
    height: int = field(default=0)          # Height of tile
    spacing: int = field(default=0)         # Spacing between tiles (all around?)
    use_mask: bool = field(default=False)   # Whether to use transparency as mask data
    separate_header_mask: bool = field(default=False)
    add_dimensions: bool = field(default=True)


# Calculate individaul sprite width, height, horizontal count, and vertical count
def expand_tileconfig(config: TileConfig, img: Image) -> (int, int, int, int):
    spriteWidth = config.width
    spriteHeight = config.height
    spacing = config.spacing
    
    # check for multiple frames/tiles
    if spriteWidth > 0:
        hframes = (img.size[0] - spacing) // (spriteWidth + spacing)
    else:
        spriteWidth = img.size[0] - 2 * spacing 
        hframes = 1
    if spriteHeight > 0:
        vframes = (img.size[1] - spacing) // (spriteHeight + spacing)
    else:
        spriteHeight = img.size[1] - 2* spacing
        vframes = 1
    
    return spriteWidth, spriteHeight, hframes, vframes

# Raise exceptions based on various inconsistencies when generating code (not fx data)
def validate_tileconfig_code(config: TileConfig, img: Image):
    spriteWidth, spriteHeight, hframes, vframes = expand_tileconfig(config, img)
    if spriteWidth > 255 or spriteHeight > 255:
        raise Exception("Image frames too large for code generation! Must be < 256 in both dimensions (per frame)!")
    if spriteWidth == 0 or spriteHeight == 0:
        raise Exception("Can't generate images with a 0-length side!")

# Raise exceptions based on various inconsistencies when generating fx data (not code)
def validate_tileconfig_fx(config: TileConfig, img: Image):
    spriteWidth, spriteHeight, hframes, vframes = expand_tileconfig(config, img)
    if spriteWidth == 0 or spriteHeight == 0:
        raise Exception("Can't generate images with a 0-length side!")


# Convert the given image (already loaded) to the header data + fxdata
# (returns a tuple). Taken almost directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/image-converter.py
def convert_image(img: Image, name: str, config: TileConfig = None) -> (str, bytearray):
    if not config:
        config = TileConfig()
    spriteName = slugify.slugify(name, lowercase=False).replace("-","_")
    img = img.convert("RGBA")
    pixels = list(img.getdata())

    spriteWidth, spriteHeight, hframes, vframes = expand_tileconfig(config, img)

    # NOTE: images with sizes larger than uint8_t are technically invalid for the code generation,
    # BUT valid for fx generation. As such, we let them be
    
    spacing = config.spacing
    transparency = config.use_mask

    #create byte array for bin file
    size = (spriteHeight+7) // 8 * spriteWidth * hframes * vframes
    bytes = bytearray([spriteWidth >> 8, spriteWidth & 0xFF, spriteHeight >> 8, spriteHeight & 0xFF])
    bytes += bytearray(size + (size if transparency else 0))
    i = 4

    headerfile = io.StringIO()
    headermask = io.StringIO()  # We track the separate mask even if we don't end up using it.

    headerfile.write("constexpr uint8_t {}Width = {};\n".format(spriteName, spriteWidth))
    headerfile.write("constexpr uint8_t {}Height = {};\n".format(spriteName,spriteHeight))
    headerfile.write("\n")
    headerfile.write("constexpr uint8_t {}[] PROGMEM\n".format(spriteName,))
    headerfile.write("{\n")

    if config.add_dimensions:
        headerfile.write("  {}Width, {}Height,\n\n".format(spriteName, spriteName))

    headermask.write(f"constexpr uint8_t {spriteName}_Mask[] PROGMEM\n{{\n")

    fy = spacing
    frames = 0

    for v in range(vframes):
        fx = spacing
        for h in range(hframes):
            headerfile.write("  //Frame {}\n".format(frames))
            headermask.write("  //Mask Frame {}\n".format(frames))
            for y in range (0,spriteHeight,8):
                line = "  "
                maskline = "  "
                for x in range (0,spriteWidth):
                    b = 0
                    m  = 0
                    for p in range (0,8):
                        b = b >> 1  
                        m = m >> 1
                        if (y + p) < spriteHeight: #for heights that are not a multiple of 8 pixels
                            pindex = (fy + y + p) * img.size[0] + fx + x
                            if pixels[pindex][1] > IMAGE_THRESHOLD:
                                b |= 0x80 #white pixel
                            if pixels[pindex][3] > ALPHA_THRESHOLD:
                                m |= 0x80 #opaque pixel
                            else:
                                b &= 0x7F #for transparent pixel clear possible white pixel 
                    bytes[i] = b
                    i += 1
                    line += "0x{:02X}, ".format(b)
                    maskline += "0x{:02X}, ".format(m)
                    if transparency: 
                        # Must always interleave bytes of fx data, regardless of 'separate mask'
                        bytes[i] = m 
                        i += 1
                        # But you interleave header only if not separate set!
                        if not config.separate_header_mask:
                            line += "0x{:02X}, ".format(m)
                lastline = (v+1 == vframes) and (h+1 == hframes) and (y+8 >= spriteHeight)
                if lastline:
                    line = line [:-2]
                    maskline = maskline[:-2]
                headerfile.write(line + "\n")
                headermask.write(maskline + "\n")
            if not lastline: 
                headerfile.write("\n")
                headermask.write("\n")
            frames += 1  
            fx += spriteWidth + spacing
        fy += spriteHeight + spacing

    headerfile.write("};\n")
    headermask.write("};\n")

    # We've been tracking mask separately. Go ahead and add the separate mask to the final data
    # if that's the exact config desired.
    if transparency and config.separate_header_mask:
        headermask.seek(0)
        headerfile.write("\n" + headermask.read())
        # bytes += maskbytes # Add maskbytes to end of byte array

    headerfile.seek(0)
        
    return headerfile.read(),bytes
    