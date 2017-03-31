# coding: utf-8

# Author: Xset
# Version: 1.0.4
# Last updated: 2017-03-24

import re
import os
import sys
import struct
import sqlite3
import binascii
import urllib3
import subprocess

from PIL import Image,  ImageDraw
from modules import *

compileDir = './compile/'
compiledDir = './compiled/'

findFiles = {}
picCount = 0

# Database connection
dbcon = sqlite3.connect("PixelData.db")
dbcon.isolation_level = None
dbcur = dbcon.cursor()
dbcon.row_factory = sqlite3.Row
dbcon.text_factory = str

urllib3.disable_warnings()

# Special class
class BytesWriter:
    
    def __init__(self, fileName):
        self.fileName = fileName
        self.handler = None
    
    def WStart(self):
        self.handler = open(self.fileName, "wb+")

    def WStop(self):
        self.handler.close()

    def WBytes(self, value):
        self.handler.write(bytes)

    def WByte(self, value):
        self.handler.write(struct.pack('<b', int(value)))

    def WUnsignedByte(self, value):
        self.handler.write(struct.pack('<B', int(value)))

    def W4Bytes(self, b, bb, bbb, bbbb):
        self.handler.write(struct.pack('4B', b, bb, bbb, bbbb))

    def WShort(self, value):
        self.handler.write(struct.pack('<h', int(value)))

    def WUnsignedShort(self, value):
        self.handler.write(struct.pack('<H', int(value)))

    def WInt(self, value):
        self.handler.write(struct.pack('<i', int(value)))

    def WUnsignedInt(self, value):
        self.handler.write(struct.pack('<I', int(value)))

    def WBool(self, value):
        self.handler.write(struct.pack('<?', int(value)))

# Latest database
def downloadDB():
    http = urllib3.PoolManager()
    
    _('Downloading the latest database...')
    response = http.request('GET', 'http://github.com/Xset-s/png2sc/raw/master/PixelData.db')
    database = response.data
    _('The latest database successfully downloaded.' + "\n")

    dbFile = open("PixelData.db", "wb+")
    dbFile.write(database)
    dbFile.close()

if not os.path.exists('PixelData.db'):
    downloadDB()

def checkAlreadyExists(filename):
    dbcur.execute('select * from PixelType where filename = ?', [filename])
    rrf = dbcur.fetchone()
    
    if rrf is None:
        return None
    
    return rrf

# Useful functions :)
def file2bytes(fileName):
    with open(fileName, "rb+") as handle:
        bytes = handle.read()

    return bytes

def bytes2file(bytes, fileName):
    handler = open(fileName, "wb+")
    handler.write(bytes)
    handler.close()

def writeImage(file, baseName, fileName, pp = 1):
    _("Collecting information...")

    # Open image
    image = Image.open(file)
    data = checkAlreadyExists(baseName)

    # Get data from database
    if not data is None:
        fileType = data[1]
        subType = data[2]
    else:
        _("Sorry, we can\'t find this texture in out database... May be you changed filename?")
        _("We will use standart fileType, subType and headerBytes. (1, 0, None)" + "\n")
        
        fileType = 1
        subType = 0
    
    # Height and width
    width  = image.size[0]
    height = image.size[1]

    pixels = []
    iSrcPix = 0

    # BPixelSize
    if subType == 0:
        BFPXFormat = 4
    elif subType == 2 or subType == 4 or subType == 6:
        BFPXFormat = 2
    elif subType == 10:
        BFPXFormat = 1
    else:
        _("Unknown pixel type %s" % (subType))
        sys.exit(0)
        
    if BFPXFormat:
        packetSize = ((width) * (height) * BFPXFormat) + 5;
    
    _("About: fileType %s, fileSize: %s, subType: %s, width: %s, height: %s" % (fileType, packetSize, subType, width, height) + "\n")
    
    imgl = image.load()
    
    if fileType == 28 or fileType == 27:
        for y in range(0, height):
            for x in range(0, width):
                c = image.getpixel((x, y))
                pixels.append(c)

        for l in range(int(height / 32)):
            for k in range(int(width / 32)):
                for j in range(32):
                    for h in range(32):
                        pixels[iSrcPix] = imgl[h + (k * 32), j + (l * 32)]
                        iSrcPix += 1
                        
            for j in range(32):
                for h in range(width % 32):
                    pixels[iSrcPix] = imgl[h + (width - (width % 32)), j + (l * 32)]
                    iSrcPix += 1

        for k in range(int(width / 32)):
            for j in range(int(height % 32)):
                for h in range(32):
                    pixels[iSrcPix] = imgl[h + (k * 32), j + (height - (height % 32))]
                    iSrcPix += 1

        for j in range(height % 32):
            for h in range(width % 32):
                pixels[iSrcPix] = imgl[h + (width - (width % 32)), j + (height - (height % 32))]
                iSrcPix += 1

    image.putdata(pixels)
    
    # Create new packet
    p = BytesWriter(fileName)

    # Start Handler
    p.WStart()

    # Packet
    p.WByte(28)
    p.WUnsignedInt(packetSize)
    p.WByte(subType)
    p.WUnsignedShort(width)
    p.WUnsignedShort(height)

    for y in range(0, height):
        for x in range(0, width):

            # Get Pixel
            c = image.getpixel((x, y))
                
            r = c[0]
            g = c[1]
            b = c[2]
            a = c[3]

            if subType == 0:
                p.W4Bytes(r, g, b, a)
                
            elif subType == 2: # RGB4444 to RGB8888
                val = 0
                
                val += int(a / 0x11) 
                val += int(b / 0x11) << 4                         
                val += int(g / 0x11) << 8
                val += int(r / 0x11) << 12

                p.WUnsignedShort(val)
                
            elif subType == 4: # RGB565 to RGB8888

                red = (r >> 3) << 11
                green = (g >> 2) << 5
                blue = b >> 3

                val = blue | green | red
                p.WUnsignedShort(val)

            elif subType == 6: # RGB555 to RGB8888
                red = r << 16
                green = g << 9
                blue = b << 6
                alpha = a << 3

                val = red | green | blue | alpha
                
                p.WUnsignedShort(val)

            elif subType == 10:
                val = b | g | r

                p.WUnsignedByte(val)
    #_(fileName)
    if fileName.endswith((pp * "_") + "tex.sc"):
        # End :c
        p.WByte(0)
        p.WByte(0)
        p.WByte(0)
        p.WByte(0)
        p.WByte(0)

    p.WStop()

def compressLZMA(fileName):
    _("Saving as sprite...")
    
    result = subprocess.call(["lzma.exe", "e", "temp_tex.sc", "temp_.tex_sc"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        result.check_returncode()
    except:
        _("ERROR. Check lzma.exe")
    
    os.remove("temp_tex.sc")
    os.rename("temp_.tex_sc", "temp_tex.sc")
    
    # Module with LZMA
    with open("temp_tex.sc", "rb") as lz:
        lzModule = lz.read()
        lzModule = lzModule[0:9] + lzModule[13:]

        mModule = open("./compiled/" + re.sub("\_*tex\_*", "_tex.sc", fileName), "wb+")
        mModule.write(lzModule)
        mModule.close()
        
        lz.close()
        os.remove("temp_tex.sc")

        _("Saving completed" + "\n")

# Parse all files from dir
def generateFilesList(dir):
    if findFiles.get(dir) is None:
        findFiles[dir] = []
                
    toCompile = os.listdir(dir)

    for file in toCompile:
        fullname = dir + file
        if os.path.isdir(fullname):
            dir_ = fullname + "/"
            
            if findFiles.get(dir_) is None:
                findFiles[dir_] = []
                
            generateFilesList(dir_)
        else:
            if file.endswith("png"):
                findFiles[dir].append(file)

generateFilesList(compileDir)

for dirName in findFiles:
    for file in findFiles[dirName]:
        file = dirName + file
        baseName, ext = os.path.splitext(os.path.basename(file))
        
        # If we will compile 2 files in one
        if not dirName == compileDir:            
            fileName = "temp_" + ("_" * picCount) + "tex.sc"
            writeImage(file, baseName, fileName, len(findFiles[dirName]))

            picCount += 1

            if picCount == len(findFiles[dirName]):
                b_bytes = b''
                
                for j in range(picCount):
                    f_name = "temp_" + ("_" * j) + "tex.sc"
                    b_bytes += file2bytes(f_name)
                    os.remove(f_name)
                    
                bytes2file(b_bytes, "temp_tex.sc")
                compressLZMA(baseName)
                    
        # if we have standart file (1 file)
        elif file.endswith("png"):
            
            fileName = "temp_tex.sc"
            writeImage(file, baseName, fileName)
            
            compressLZMA(baseName)
