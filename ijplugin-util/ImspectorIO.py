'''
Commonly needed functions for handling Imspector .msr files

started 4/29/2015
David Hoerl
'''

from loci.plugins import BF

# manually import ImporterOptions, as the package name contains the "in" constant
ImporterOptions = __import__("loci.plugins.in.ImporterOptions", globals(), locals(), ['object'], -1)

from ij import ImagePlus
from ij import IJ

from java.lang import Integer, Short

from glob import glob
import os
import struct
import array
import csv


def openMSR(path):
    '''
    open a .msr file, get list of images
    '''
    try:
        io = ImporterOptions()
        io.setId(path)
        io.setOpenAllSeries(True)
        imps = BF.openImagePlus(io) 
        return imps   
    except ImagePlus:
        IJ.log("ERROR while opening image file " + path)
        
def impToFloatPixels(imp):
    '''
    convert image to 32bit to get meaningful values
    '''
    pixels = imp.getProcessor().convertToFloatProcessor().getPixels()
    return pixels

def writePixelsToCSV(fd, pix, prefixes, delim=";", seperator="."):
    for p in pix:
        fd.write(delim.join(prefixes) + delim + str(p).replace(".", seperator) + "\n")