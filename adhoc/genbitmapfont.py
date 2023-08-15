from PIL import Image, ImageDraw, ImageFont

import os

FONTWIDTH = 4
FONTHEIGHT = 7
FONTSIZE = 16

CHARS = 256
PERLINE = 16
LINES = CHARS // PERLINE

WORKFOLDER = "appresource"

font = os.path.join(WORKFOLDER, "m3x6.ttf")
chars = "".join([chr(byte) for byte in range(0,CHARS)])

img = Image.new('1', (FONTWIDTH * PERLINE, FONTHEIGHT * LINES), 0)  # 1-bit black and white image
font = ImageFont.truetype(font, FONTSIZE) # I think the thing said 16, 32, etc
draw = ImageDraw.Draw(img)

for index, c in enumerate(chars):
    x = (index % PERLINE) * FONTWIDTH
    y = (index // PERLINE) * FONTHEIGHT
    draw.text((x, y), str(c), font=font, fill=1)

img.save(os.path.join(WORKFOLDER, "m3x6.png"))
