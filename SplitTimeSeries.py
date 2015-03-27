import os
import re
import sys
import gc

from ij import IJ
from ij import ImagePlus
from ij import ImageStack
from ij import ImageJ
from ij.process import ImageProcessor
from ij.io import DirectoryChooser


# USER INPUT
slicesPerTimepoint = 151


# let user select directory, use only this directory (not subdirectories)
dc = DirectoryChooser("Choose directory to process.")
inputPath = dc.getDirectory()

dirs = os.walk(inputPath)
inputDir = dirs.next()


if not os.path.exists(os.path.join(inputPath, "timepoints")):
    os.makedirs(os.path.join(inputPath, "timepoints"))

# pattern of the image files
p = re.compile("(.*?Pos[0-9])(.*?\.ome\.tif)")

# map all image file prefixes (corresponding to angles)
# to all files starting with it (containing the timepoints)
prefixes = dict()

for f in inputDir[2]:
    m = p.match(f)
    
    # file matches pattern
    if m:
        
        # new prefix
        if not m.groups()[0] in prefixes:
            prefixes[m.groups()[0]] = list()
        
        # add new suffix to dict for prefix  
        prefixes[m.groups()[0]].append(m.groups()[1])


for prefix, suffix in prefixes.items():
    
    # open first image to create stack (copy dimensions etc.)
    firstImg = IJ.openImage(os.path.join(inputPath, prefix + suffix[0]))
    
    tpStack = firstImg.createEmptyStack()    
    tpNr = 0
    
    # to deallocate image
    firstImg = None
    gc.collect()
    
    for s in suffix:
        img = IJ.openImage(os.path.join(inputPath, prefix + s))

        for i in range(1, img.getNSlices()+1):
            img.setSlice(i)
            tpStack.addSlice(img.getProcessor())
            
            if tpStack.getSize() == slicesPerTimepoint:
                outImg = ImagePlus("Timepoint " + str(tpNr), tpStack)
                IJ.saveAsTiff(outImg , os.path.join(inputPath, "timepoints", prefix + "_TP" + str(tpNr) + ".ome.tif"))
                tpStack = img.createEmptyStack()
                tpNr += 1

        # to deallocate image
        img = None
        gc.collect()
    
    # save last Timepoint (possibly incomplete)
    outImg = ImagePlus("Timepoint " + str(tpNr), tpStack)
    IJ.saveAsTiff(outImg , os.path.join(inputPath, "timepoints", prefix + "_TP" + str(tpNr) + ".ome.tif"))
            

#sys.exit()