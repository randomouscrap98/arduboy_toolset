#FX data build tool version 1.15 by Mr.Blinky May 2021 - Mar.2023
# Modified slightly to work with arduboy toolset

VERSION = '1.15'

import os
import re
import platform

import logging

from PIL import Image

constants = [
  #normal bitmap modes
  ("dbmNormal",    0x00),
  ("dbmOverwrite", 0x00),
  ("dbmWhite",     0x01),
  ("dbmReverse",   0x08),
  ("dbmBlack",     0x0D),
  ("dbmInvert",    0x02),
  #masked bitmap modes for frame
  ("dbmMasked",              0x10),
  ("dbmMasked_dbmWhite",     0x11),
  ("dbmMasked_dbmReverse",   0x18),
  ("dbmMasked_dbmBlack",     0x1D),
  ("dbmMasked_dbmInvert",    0x12),
  #bitmap modes for last bitmap in a frame
  ("dbmNormal_end",    0x40),
  ("dbmOverwrite_end", 0x40),
  ("dbmWhite_end",     0x41),
  ("dbmReverse_end",   0x48),
  ("dbmBlack_end",     0x4D),
  ("dbmInvert_end",    0x42),
  #masked bitmap modes for last bitmap in a frame
  ("dbmMasked_end",              0x50),
  ("dbmMasked_dbmWhite_end",     0x51),
  ("dbmMasked_dbmReverse_end",   0x58),
  ("dbmMasked_dbmBlack_end",     0x5D),
  ("dbmMasked_dbmInvert_end",    0x52),
  #bitmap modes for last bitmap of the last frame
  ("dbmNormal_last",    0x80),
  ("dbmOverwrite_last", 0x80),
  ("dbmWhite_last",     0x81),
  ("dbmReverse_last",   0x88),
  ("dbmBlack_last",     0x8D),
  ("dbmInvert_last",    0x82),
  #masked bitmap modes for last bitmap in a frame
  ("dbmMasked_last",              0x90),
  ("dbmMasked_dbmWhite_last",     0x91),
  ("dbmMasked_dbmReverse_last",   0x98),
  ("dbmMasked_dbmBlack_last",     0x9D),
  ("dbmMasked_dbmInvert_last",    0x92),
]


class FxBuildData:

  def __init__(self, fxdata_path):
    self.symbols = []
    self.header = []
    self.indent = ''
    self.filename = os.path.abspath(fxdata_path)
    self.path = os.path.dirname(self.filename) + os.sep

  def rawData(self, filename):
    with open(self.path + filename,"rb") as file:
      return bytearray(file.read())

  def includeFile(self, filename):
    logging.info("Including file {}".format(self.path + filename))
    with open(self.path + filename,"r") as file:
      return file.readlines()

  def writeHeader(self, s):
    self.header.append(s)

  def imageData(self, filename):
    filename = self.path + filename
    ## parse filename ## FILENAME_[WxH]_[S].[EXT]"
    spriteWidth = 0
    spriteHeight = 0
    spacing = 0
    elements = os.path.basename(os.path.splitext(filename)[0]).split("_")
    lastElement = len(elements)-1
    #get width and height from filename
    i = lastElement
    while i > 0:
      subElements = list(filter(None,elements[i].split('x')))
      if len(subElements) == 2 and subElements[0].isnumeric() and subElements[1].isnumeric():
        spriteWidth = int(subElements[0])
        spriteHeight = int(subElements[1])
        if i < lastElement and elements[i+1].isnumeric():
          spacing = int(elements[i+1])
        break
      else: 
        i -= 1

    #load image
    img = Image.open(filename).convert("RGBA")
    pixels = list(img.getdata())
    #check for transparency
    transparency = False
    for i in pixels:
      if i[3] < 255:
        transparency = True
        break

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
    fy = spacing
    frames = 0
    for v in range(vframes):
      fx = spacing
      for h in range(hframes):
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
            i += 1
            if transparency:
              bytes[i] = m
              i += 1
        frames += 1
        fx += spriteWidth + spacing
      fy += spriteHeight + spacing
    label = self.symbols[-1][0]
    if label.upper() == label:
      self.writeHeader('{}constexpr uint16_t {}_WIDTH  = {};'.format(self.indent,label,spriteWidth))
      self.writeHeader('{}constexpr uint16_t {}HEIGHT  = {};'.format(self.indent,label,spriteHeight))
      if frames > 1: 
        self.writeHeader('{}constexpr uint8_t  {}_FRAMES = {};'.format(self.indent,label,frames))
    elif '_' in label:
      self.writeHeader('{}constexpr uint16_t {}_width  = {};'.format(self.indent,label,spriteWidth))
      self.writeHeader('{}constexpr uint16_t {}_height = {};'.format(self.indent,label,spriteHeight))
      if frames > 1: 
        self.writeHeader('{}constexpr uint8_t  {}_frames = {};'.format(self.indent,label,frames))
    else:
      self.writeHeader('{}constexpr uint16_t {}Width  = {};'.format(self.indent,label,spriteWidth))
      self.writeHeader('{}constexpr uint16_t {}Height = {};'.format(self.indent,label,spriteHeight))
      if frames > 255: 
        self.writeHeader('{}constexpr uint16_t  {}Frames = {};'.format(self.indent,label,frames))
      elif frames > 1: 
        self.writeHeader('{}constexpr uint8_t  {}Frames = {};'.format(self.indent,label,frames))
    self.writeHeader('')
    return bytes

  def addLabel(self, label,length):
    self.symbols.append((label,length))
    self.writeHeader('{}constexpr uint24_t {} = 0x{:06X};'.format(self.indent,label,length))



def build_fx(fxdata_file):
  logging.info('FX data build tool version {} by Mr.Blinky May 2021 - Jan 2023\nUsing Python version {}'.format(VERSION,platform.python_version()))

  fxbuilder = FxBuildData(fxdata_file)

  bytes = bytearray()
  label = ''
  blkcom = False
  namespace = False
  include = False

  # These should probably be configurable later
  datafilename = os.path.splitext(fxbuilder.filename)[0] + '-data.bin'
  savefilename = os.path.splitext(fxbuilder.filename)[0] + '-save.bin'
  devfilename = os.path.splitext(fxbuilder.filename)[0] + '.bin'
  headerfilename = os.path.splitext(fxbuilder.filename)[0] + '.h'
  saveStart = -1

  with open(fxbuilder.filename,"r") as file:
    lines = file.readlines()

  logging.info("Building FX data using {}".format(fxbuilder.filename))
  lineNr = 0
  while lineNr < len(lines):
    parts = [p for p in re.split("([ ,]|[\\'].*[\\'])", lines[lineNr]) if p.strip() and p != ',']
    for i in range (len(parts)):
      part = parts[i]
      #strip unwanted chars
      if part[:1]  == '\t' : part = part[1:]
      if part[:1]  == '{' : part = part[1:]
      if part[-1:] == '\n': part = part[:-1]
      if part[-1:] == ';' : part = part[:-1]
      if part[-1:] == '}' : part = part[:-1]
      if part[-1:] == ';' : part = part[:-1]
      if part[-1:] == '.' : part = part[:-1]
      if part[-1:] == ',' : part = part[:-1]
      if part[-2:] == '[]': part = part[:-2]
      #handle comments
      if blkcom == True:
        p = part.find('*/',2)
        if p >= 0:
          part = part[p+2:]
          blkcom = False
      else:
        if   part[:2] == '//':
          break
        elif part[:2] == '/*':
          p = part.find('*/',2)
          if p >= 0: part = part[p+2:]
          else: blkcom = True;
        #handle types
        elif part == '='       : pass
        elif part == 'const'   : pass
        elif part == 'PROGMEM' : pass
        elif part == 'align'   : t = 0
        elif part == 'int8_t'  : t = 1
        elif part == 'uint8_t' : t = 1
        elif part == 'int16_t' : t = 2
        elif part == 'uint16_t': t = 2
        elif part == 'int24_t' : t = 3
        elif part == 'uint24_t': t = 3
        elif part == 'int32_t' : t = 4
        elif part == 'uint32_t': t = 4
        elif part == 'image_t' : t = 5
        elif part == 'raw_t'   : t = 6
        elif part == 'String'  : t = 7
        elif part == 'string'  : t = 7
        elif part == 'include' : include = True
        elif part == 'datasection'  : pass
        elif part == 'savesection'  : saveStart = len(bytes)
        #handle namespace
        elif part == 'namespace':
          namespace = True
        elif namespace == True:
          namespace = False      
          fxbuilder.writeHeader("namespace {}\n{{".format(part))
          fxbuilder.indent += '  '
        elif part == 'namespace_end':
          fxbuilder.indent = fxbuilder.indent[:-2]
          fxbuilder.writeHeader('}\n')
          namespace = False
        #handle strings
        elif (part[:1] == "'") or (part[:1] == '"'):
          if  part[:1] == "'": 
            part = part[1:part.rfind("'")]
          else:  
            part = part[1:part.rfind('"')]
          #handle include
          if include == True:
            lines[lineNr+1:lineNr+1] = fxbuilder.includeFile(part)      
            include = False
          elif t == 1: bytes += part.encode('utf-8').decode('unicode_escape').encode('utf-8')
          elif t == 5: bytes += fxbuilder.imageData(part)
          elif t == 6: bytes += fxbuilder.rawData(part)
          elif t == 7: bytes += part.encode('utf-8').decode('unicode_escape').encode('utf-8') + b'\x00'
          else: raise Exception('ERROR in line {}: unsupported string for type\n'.format(lineNr))
        #handle values
        elif part[:1].isnumeric() or (part[:1] == '-' and part[1:2].isnumeric()):
          n = int(part,0)
          if t == 4: bytes.append((n >> 24) & 0xFF)
          if t >= 3: bytes.append((n >> 16) & 0xFF)
          if t >= 2: bytes.append((n >> 8) & 0xFF)
          if t >= 1: bytes.append((n >> 0) & 0xFF)
        #handle align
          if t == 0:
            align = len(bytes) % n
            if align: bytes += b'\xFF' * (n - align)
        #handle labels
        elif part[:1].isalpha():
          for j in range(len(part)):
            if part[j] == '=':
              fxbuilder.addLabel(label,len(bytes))
              label = ''
              part = part[j+1:]
              parts.insert(i+1,part)
              break
            elif part[j].isalnum() or part[j] == '_':
              label += part[j]
            else:
              raise Exception('ERROR in line {}: Bad label: {}\n'.format(lineNr,label))
          if (label != '') and (i < len(parts) - 1) and (parts[i+1][:1] == '='):
            fxbuilder.addLabel(label,len(bytes))
            label = ''
          #handle included constants
          if label != '':
            for symbol in constants:
              if symbol[0] == label:
                if t == 4: bytes.append((symbol[1] >> 24) & 0xFF)
                if t >= 3: bytes.append((symbol[1] >> 16) & 0xFF)
                if t >= 2: bytes.append((symbol[1] >> 8) & 0xFF)
                if t >= 1: bytes.append((symbol[1] >> 0) & 0xFF)
                label = ''
                break
          #handle symbol values
          if label != '':
            for symbol in fxbuilder.symbols:
              if symbol[0] == label:
                if t == 4: bytes.append((symbol[1] >> 24) & 0xFF)
                if t >= 3: bytes.append((symbol[1] >> 16) & 0xFF)
                if t >= 2: bytes.append((symbol[1] >> 8) & 0xFF)
                if t >= 1: bytes.append((symbol[1] >> 0) & 0xFF)
                label = ''
                break
          if label != '':
            raise Exception('ERROR in line {}: Undefined symbol: {}\n'.format(lineNr,label))
        elif len(part) > 0:
          raise Exception('ERROR unable to parse {} in element: {}\n'.format(part,str(parts)))
    lineNr += 1

  if saveStart >= 0:
    dataSize  = saveStart
    dataPages = (dataSize + 255) // 256
    saveSize = len(bytes) - saveStart
    savePages = (saveSize + 4095) // 4096 * 16
  else:
    dataSize  = len(bytes)
    dataPages = (dataSize + 255) // 256
    saveSize  = 0
    savePages = 0
    savePadding = 0
  dataPadding = dataPages * 256 - dataSize
  savePadding = savePages * 256 - saveSize

  writefiles = {
    "header" : headerfilename,
    "data" : datafilename,
    "dev" : devfilename
  }

  logging.info("Saving FX data header file {}".format(headerfilename))
  with open(headerfilename,"w") as file:
    file.write('#pragma once\n\n')
    file.write('/**** FX data header generated by fxdata-build.py tool version {} ****/\n\n'.format(VERSION))
    file.write('using uint24_t = __uint24;\n\n')
    file.write('// Initialize FX hardware using  FX::begin(FX_DATA_PAGE); in the setup() function.\n\n')
    file.write('constexpr uint16_t FX_DATA_PAGE  = 0x{:04x};\n'.format(65536 - dataPages - savePages))
    file.write('constexpr uint24_t FX_DATA_BYTES = {};\n\n'.format(dataSize))
    if saveSize > 0: 
      file.write('constexpr uint16_t FX_SAVE_PAGE  = 0x{:04x};\n'.format(65536 - savePages))
      file.write('constexpr uint24_t FX_SAVE_BYTES = {};\n\n'.format(saveSize))
    for line in fxbuilder.header:
      file.write(line + '\n')

  logging.info("Saving {} bytes FX data to {}".format(dataSize,datafilename))
  with open(datafilename,"wb") as file:
    file.write(bytes[0:dataSize])
  if saveSize > 0:
    writefiles["save"] = savefilename
    logging.info("Saving {} bytes FX savedata to {}".format(saveSize,savefilename))
    with open(savefilename,"wb") as file:
      file.write(bytes[saveStart:len(bytes)])
  logging.info("Saving FX development data to {}".format(devfilename))
  with open(devfilename,"wb") as file:
    file.write(bytes[0:dataSize])
    if dataPadding > 0: file.write(b'\xFF' * dataPadding)
    if saveSize > 0:
      file.write(bytes[saveStart:len(bytes)])
      if savePadding > 0: file.write(b'\xFF' * savePadding)

  return writefiles