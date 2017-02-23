# coding: utf-8

import os
import struct
import lzma

from PIL import Image,  ImageDraw
from modules import *

compileDir = './compile/'
compiledDir = './compiled/'

headerBytes = b'SC\x00\x00\x00\x01\x00\x00\x00\x100\\c\x95\x01@E\xf0\xb1\xc2\xa6\xf4\x08Kkk'

toCompile = os.listdir(compileDir)

def __():
    print("")
    
def _(message):
    print(u"[DEBUG] %s" % message)

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
        _('PacketSize: ' + str(packetSize))
        __()
        
        # Create new packet
        p = ByteArray()

        # Формируем пакет
        p.writeByte(1)
        p.writeUnsignedInt(packetSize)
        p.writeByte(0)
        p.writeUnsignedShort(width)
        p.writeUnsignedShort(height)
        
        data = p.toByteArray()

        # Temp file
        cModule = open("temp.tex_sc", "wb+")
        cModule.write(data)
        
        _( 'Saving _tex.sc...' )
        
        for y in range(0, height):
            for x in range(0, width):  
                c = image.getpixel((x, y))
                
                r = c[0]
                g = c[1]
                b = c[2]
                a = c[3]
                
                cModule.write(struct.pack('<B', r))
                cModule.write(struct.pack('<B', g))
                cModule.write(struct.pack('<B', b))
                cModule.write(struct.pack('<B', a))

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

            mModule = open('./compiled/' + baseName + '_tex.sc', "wb+")
            mModule.write(lzModule)
            mModule.close()
            _( 'Saving OK...' )            

            lz.close()

            os.remove("temp.tex_sc")
            
            
