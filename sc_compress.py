# coding: utf-8
# Author: Xset

import os
import lzma
import math
import struct
import sqlite3
import urllib3
import binascii

from PIL import Image,  ImageDraw
from modules import *

compileDir = './compile/'
compiledDir = './compiled/'

# Set OFF SSL warnings (because we will download from github)
urllib3.disable_warnings()

toCompile = os.listdir(compileDir)

def _(message):
    print(u"[RELEASE] %s" % message)

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

# Database connection
dbcon = sqlite3.connect("PixelData.db")
dbcon.isolation_level = None
dbcur = dbcon.cursor()
dbcon.row_factory = sqlite3.Row
dbcon.text_factory = str

def checkAlreadyExists(filename):
    dbcur.execute('select * from PixelType where filename = ?', [filename])
    rrf = dbcur.fetchone()
    
    if rrf is None:
        return None
    
    return rrf

def float2int(flt):
    return int(math.ceil(flt))

for file in toCompile:
    baseName, ext = os.path.splitext(os.path.basename(file))
    file = compileDir + file
    if file.endswith('png'):
        _('FileName: ' + file)
        image = Image.open(file)
        
        width  = image.size[0]
        height = image.size[1]

        _('Width: ' + str(width))
        _('Height: ' + str(height))
        
        BFPXFormat = 4

        # Size
        packetSize = ((width) * (height) * BFPXFormat) + 5;
        _('PacketSize: ' + str(packetSize) + "\n")

        # Get data from database
        data = checkAlreadyExists(baseName)
        
        if not data is None:
            subType = data[1]
            headerBytes = binascii.unhexlify(data[2])
        else:
            _('Sorry, we can\'t find this texture in out database... May be you changed filename?')
            _('We will use standart subType and headerBytes. (0, None)' + "\n")

            subType = 0
            headerBytes = b''
            
        # Create new packet
        p = ByteArray()

        # Формируем пакет
        p.writeByte(1)
        p.writeUnsignedInt(packetSize)
        p.writeByte(subType)
        p.writeUnsignedShort(width)
        p.writeUnsignedShort(height)
        
        data = p.toByteArray()

        # Temp file
        cModule = open("temp.tex_sc", "wb+")
        cModule.write(data)
        
        _( 'Saving _tex.sc...' )
        
        for y in range(0, height):
            for x in range(0, width):

                # Get Pixel
                c = image.getpixel((x, y))
                    
                r = c[0]
                g = c[1]
                b = c[2]
                a = c[3]

                # Write pixel in file
                if subType == 0:                    
                    cModule.write(struct.pack('4B', r, g, b, a))
                # RGB4444
                elif subType == 2:
                    pack = 0
                    
                    pack += int(a / 0x11) 
                    pack += int(b / 0x11) << 4                         
                    pack += int(g / 0x11) << 8
                    pack += int(r / 0x11) << 12

                    cModule.write(struct.pack('<H', val))
                    
        cModule.close()

        _( 'Compressing data...' )
        os.system('lzma.exe e temp.tex_sc temp_.tex_sc')
        _( 'Compressing OK...' )

        os.remove('temp.tex_sc')
        os.rename('temp_.tex_sc', 'temp.tex_sc')
        
        # Module with LZMA
        with open('temp.tex_sc', 'rb') as lz:
            lzModule = lz.read()
            lzModule = lzModule[0:9] + lzModule[13:]

            # Add headers
            lzModule = headerBytes + lzModule

            mModule = open('./compiled/' + baseName + '.sc', "wb+")
            mModule.write(lzModule)
            mModule.close()
            _( 'Saving OK...' )            

            lz.close()

            os.remove("temp.tex_sc")
