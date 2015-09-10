'''
Scripts to analyze crosstalk between 2 channels (Imspector measurements)

started 4/16/2015
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


def analyzeCrosstalk(imps, channelIndices, baseChannel, bgImps = None):
    
    sums = dict()
    
    for i in channelIndices:
        sums[i] = imps[i].getStatistics().mean
        
    if bgImps:
        for i in channelIndices:
            sums[i] -= bgImps[i].getStatistics().mean
            
    baseSignal = sums[baseChannel]
    
    for i in sums.keys():
        sums[i] /= baseSignal
        
    return sums

def openMSR(path):
    try:
        io = ImporterOptions()
        io.setId(path)
        io.setOpenAllSeries(True)
        imps = BF.openImagePlus(io) 
        return imps   
    except ImagePlus:
        IJ.log("ERROR while opening image file " + path)

def main0416():
    '''
    main for analysis of 2015/04/16 dataset
    '''
    filePath = "/Users/david/Desktop/20150415_A594_Crosstalk"
    fileEnding = ".msr"
    
    outFile = os.path.join(filePath, "res.csv")
    
    csvfile = open(outFile, "w")
    writer = None
    
    
    # get full paths of all files in filePath ending with fileEnding
    files = [os.path.join(filePath, file) for file in os.walk(filePath).next()[2] if file.endswith(fileEnding)]
    
    for f in files:
        
        imps = openMSR(f)
        res = analyzeCrosstalk(imps, [0,1,4,5], 0)
        print res
        
        if not writer:
            writer = csv.DictWriter(csvfile, delimiter=";", lineterminator="\n", fieldnames=res.keys())
            writer.writerow(dict(zip(res.keys(), res.keys())))
        
        writer.writerow(res)
    

'''
MAIN
'''
if __name__ == "__main__":
    main0416()