'''
Scripts to analyze vibrations in xt/yt scans (Imspector measurements)

started 4/17/2015
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
    try:
        io = ImporterOptions()
        io.setId(path)
        io.setOpenAllSeries(True)
        imps = BF.openImagePlus(io) 
        return imps   
    except ImagePlus:
        IJ.log("ERROR while opening image file " + path)

def getMassCenters(imp):
    # convert image to 32bit to get meaningful values
    pixels = imp.getProcessor().convertToFloatProcessor().getPixels()
    width = imp.getWidth()
    lines = list()
    
    for i in range(len(pixels)):
        if not i%width:
            lines.append(list())
        lines[-1].append(pixels[i])
        
    massCenters = list()
    for l in lines:
        massCenters.append(getMassCenter(l))
        
    return massCenters
    
def getMassCenter(v, threshold=None):
    if threshold:
        for vi in v:
            if vi < threshold:
                vi = 0
    
    sumMass = 0
    sum = 0
    for i in range(len(v)):
        sum += i * v[i]
        sumMass += v[i]
        
    res = sum/sumMass
    return res
    
    
def main0417():
    '''
    main for analysis of 2015/04/16 dataset
    '''
    filePath = "/Users/david/Desktop/20150416_Vibrations"
    fileEnding = ".msr"
    
    outFile = os.path.join(filePath, "res.txt")
    
    csvfile = open(outFile, "w")
 
    
    # get full paths of all files in filePath ending with fileEnding
    files = [os.path.join(filePath, file) for file in os.walk(filePath).next()[2] if file.endswith(fileEnding)]
    
    for f in files:
        print f
        imps = openMSR(f)
        mc = getMassCenters(imps[0])
        
        csvfile.write(f.split(os.path.sep)[-1] + " ")
        csvfile.write(" ".join(map(str, mc)) + "\n")
        
    csvfile.close()
    
'''
MAIN
'''
if __name__ == "__main__":
    main0417()