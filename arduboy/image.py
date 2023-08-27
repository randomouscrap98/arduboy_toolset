from arduboy.constants import *

import slugify
import io

from PIL import Image
from dataclasses import dataclass

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
    width: int      # Width of tile
    height: int     # Height of tile
    spacing: int    # Spacing between tiles (all around?)
    use_mask: bool  # Whether to use transparency as mask data


# Convert the given image (already loaded) to the header data + fxdata
# (returns a tuple). Taken almost directly from https://github.com/MrBlinky/Arduboy-Python-Utilities/blob/main/image-converter.py
def convert_image(image: Image, name: str, config: TileConfig = None) -> (str, bytearray):
    if not config:
        config = TileConfig()
    spriteName = slugify.slugify(name).replace("-","_")
    img = img.convert("RGBA")
    pixels = list(img.getdata())

    spriteWidth = config.width
    spriteHeight = config.height
    spacing = config.spacing
    transparency = config.use_mask
    
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
    
    #create byte array for bin file
    size = (spriteHeight+7) // 8 * spriteWidth * hframes * vframes
    if transparency:
        size += size
    bytes = bytearray([spriteWidth >> 8, spriteWidth & 0xFF, spriteHeight >> 8, spriteHeight & 0xFF])
    bytes += bytearray(size)
    i = 4
    b = 0
    m = 0

    headerfile = io.StringIO()
    
    # headerfile.write("#pragma once\n")
    headerfile.write("constexpr uint8_t {}Width = {};\n".format(spriteName, spriteWidth))
    headerfile.write("constexpr uint8_t {}Height = {};\n".format(spriteName,spriteHeight))
    headerfile.write("\n")
    headerfile.write("const uint8_t PROGMEM {}[] =\n".format(spriteName,))
    headerfile.write("{\n")
    headerfile.write("  {}Width, {}Height,\n".format(spriteName, spriteName))
    fy = spacing
    frames = 0
    for v in range(vframes):
        fx = spacing
        for h in range(hframes):
            headerfile.write("  //Frame {}\n".format(frames))
            for y in range (0,spriteHeight,8):
                line = "  "
                for x in range (0,spriteWidth):
                    for p in range (0,8):
                        b = b >> 1  
                        m = m >> 1
                        if (y + p) < spriteHeight: #for heights that are not a multiple of 8 pixels
                            if pixels[(fy + y + p) * img.size[0] + fx + x][1] > 64:
                                b |= 0x80 #white pixel
                            if pixels[(fy + y + p) * img.size[0] + fx + x][3] > 64:
                                m |= 0x80 #opaque pixel
                            else:
                                b &= 0x7F #for transparent pixel clear possible white pixel 
                    bytes[i] = b
                    line += "0x{:02X}, ".format(b)
                    i += 1
                    if transparency:
                        bytes[i] = m 
                        line += "0x{:02X}, ".format(m)
                        i += 1
                lastline = (v+1 == vframes) and (h+1 == hframes) and (y+8 >= spriteHeight)
                if lastline:
                    line = line [:-2]
                headerfile.write(line + "\n")
            if not lastline: 
                headerfile.write("\n")
            frames += 1  
            fx += spriteWidth + spacing
        fy += spriteHeight + spacing

    headerfile.write("};\n")

    headerfile.seek(0)
        
    return headerfile.read(),bytes
    