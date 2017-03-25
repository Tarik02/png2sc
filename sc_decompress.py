# coding: utf-8

# Original from https://github.com/royale-proxy/
# Rewritten by Xset

import os
import sys
import lzma
import struct
import random
import sqlite3
import urllib3
import binascii

from modules import *
from PIL import Image

# Folders
folder = "./decompile/"
folder_export = "./decompiled/"

# Disable warnings (ssl)
urllib3.disable_warnings()

# Database connection
dbcon = sqlite3.connect("PixelData.db")
dbcon.isolation_level = None
dbcur = dbcon.cursor()
dbcon.row_factory = sqlite3.Row
dbcon.text_factory = str

# Latest database
def downloadDB():
    http = urllib3.PoolManager()
    
    _("Downloading the latest database...")
    response = http.request("GET", "http://github.com/Xset-s/png2sc/raw/master/PixelData.db")
    database = response.data
    _("The latest database successfully downloaded." + "\n")

    dbFile = open("PixelData.db", "wb+")
    dbFile.write(database)
    dbFile.close()

def checkAlreadyExists(filename):
    dbcur.execute("select * from PixelType where filename = ?", [filename])
    rrf = dbcur.fetchone()
    
    if rrf is None:
        return None
    
    return 1

def convert_pixel(pixel, type):
    if type == 0:
        # RGB8888
        return struct.unpack("4B", pixel)
    elif type == 2:
        # RGB4444        
        pixel, = struct.unpack("<H", pixel)
        #print(pixel)
        return (((pixel >> 12) & 0xF) << 4, ((pixel >> 8) & 0xF) << 4,
                ((pixel >> 4) & 0xF) << 4, ((pixel >> 0) & 0xF) << 4)
    elif type == 4:
        # RGB565
        pixel, = struct.unpack("<H", pixel)
        #_(pixel)
        #_([(((pixel >> 11) & 0x1F) << 3, ((pixel >> 5) & 0x3F) << 2, (pixel & 0x1F) << 3)])
        return (((pixel >> 11) & 0x1F) << 3, ((pixel >> 5) & 0x3F) << 2, (pixel & 0x1F) << 3)
    elif type == 6:
        # RGB555?
        pixel, = struct.unpack("<H", pixel)
        
        return ((pixel >> 16) & 0x80, (pixel >> 9) & 0x7C,
                (pixel >> 6) & 0x3E, (pixel >> 3) & 0x1F)
    elif type == 10:
        # BGR233?
        pixel, = struct.unpack("<B", pixel)
        return ((pixel) & 0x3, ((pixel >> 2) & 0x7) << 2, ((pixel >> 5) & 0x7) << 5)
    else:
        raise Exception("Unknown pixel type %s." % (type))

if not os.path.exists("PixelData.db"):
    downloadDB()

files = os.listdir(folder)
for file_d in files:
    baseName, ext = os.path.splitext(os.path.basename(file_d))
    if file_d.endswith("_tex.sc"):
        with open(folder + file_d, "rb") as fh:
            data = fh.read()

            # Fix headers
            if data[0] != 93:
                data = data[26:]
                
            data = data[0:9] + (b"\x00" * 4) + data[9:]
            
            # LZMA Decompression
            _("Decompressing data...")
            decompressed = lzma.LZMADecompressor().decompress(data)
            _("Decompressing OK" + "\n")
            
            i = 0
            picCount = 0

            p = ByteArray(decompressed)

            _("Collecting information...")
            while len(decompressed[i:]) > 5:        
                fileType = decompressed[i]
                fileSize, = struct.unpack("<I", decompressed[i + 1:i + 5])
                subType = decompressed[i + 5]
                width, = struct.unpack("<H", decompressed[i + 6:i + 8])
                height, = struct.unpack("<H", decompressed[i + 8:i + 10])
                
                i += 10
                
                if subType == 0:
                    pixelSize = 4
                elif subType == 2 or subType == 4 or subType == 6:
                    pixelSize = 2
                elif subType == 10:
                    pixelSize = 1
                else:
                    raise Exception("Unknown pixel type {}.".format(subType))

                _("About: fileName %s, fileType %s, fileSize: %s, subType: %s, width: %s, height: %s" % (file_d, fileType, fileSize, subType, width, height))

                _("Creating picture...")
                img = Image.new("RGBA", (width, height))
                
                pixels = []
                for y in range(height):
                    for x in range(width):
                        pixels.append(convert_pixel(decompressed[i:i + pixelSize], subType))
                        i += pixelSize
                
                img.putdata(pixels)
                if fileType == 28 or fileType == 27:
                    imgl = img.load()
                    iSrcPix = 0
                    for l in range(int(height / 32)):  # block of 32 lines
                        # normal 32-pixels blocks
                        for k in range(int(width / 32)):  # 32-pixels blocks in a line
                            for j in range(32):  # line in a multi line block
                                for h in range(32):  # pixels in a block
                                    imgl[h + (k * 32), j + (l * 32)] = pixels[iSrcPix]
                                    iSrcPix += 1
                        # line end blocks
                        for j in range(32):
                            for h in range(width % 32):
                                imgl[h + (width - (width % 32)), j + (l * 32)] = pixels[iSrcPix]
                                iSrcPix += 1
                    # final lines
                    for k in range(int(width / 32)):  # 32-pixels blocks in a line
                        for j in range(int(height % 32)):  # line in a multi line block
                            for h in range(32):  # pixels in a 32-pixels-block
                                imgl[h + (k * 32), j + (height - (height % 32))] = pixels[iSrcPix]
                                iSrcPix += 1
                    # line end blocks
                    for j in range(height % 32):
                        for h in range(width % 32):
                            imgl[h + (width - (width % 32)), j + (height - (height % 32))] = pixels[iSrcPix]
                            iSrcPix += 1
                            
                fullname = baseName + ('_' * picCount)

                if checkAlreadyExists(fullname) is None:
                    _("Writing data in database...")
                    dbcur.execute('INSERT INTO PixelType (filename, fileType, pixel, hexsc) values (?, ?, ?, ?)', [fullname, fileType, subType, ''])
                    _("Data successfully written" + "\n")
                    
                _("Saving as png...")
                img.save(folder_export + fullname + ".png", "PNG")
                picCount += 1
                _("Saving completed" + "\n")
