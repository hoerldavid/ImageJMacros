#from Utilities import Counter3D
from mcib3d.geom import Object3D, Vector3D, Point3D
from mcib3d.geom import Object3DPoint, Object3DSurface
from mcib3d.image3d import Segment3DImage

from javax.vecmath import Point3f
from java.util import ArrayList
from java.lang import Integer

from ij.plugin import Resizer
from ij.io import DirectoryChooser, OpenDialog
from ij import IJ, ImagePlus
from ij.process import StackConverter, StackProcessor

import os
import re
import sys

def apoptosisAnalyis(pathClones, pathApo):
    
    # specify Downsampling
    downsampleXY = 1
    downsampleZ = 1
    # thresholds = 128?
    threshold = 128
    # minimum sizes
    minSizeClone = 0
    minSizeApo = 0
    
    # load images
    impClones = IJ.openImage(pathClones)
    impApo = IJ.openImage(pathApo)
    
    # convert to 8bit (TODO: set min/max?)
    StackConverter(impClones).convertToGray8()
    StackConverter(impApo).convertToGray8()

    # downsample images
    impClones = Resizer().zScale(impClones, int(impClones.getNSlices() * downsampleZ), 0)
    newW = int(impClones.getWidth() * downsampleXY)
    newH = int(impClones.getHeight() * downsampleXY)    
    impClones.setStack(StackProcessor(impClones.getStack()).resize(newW, newH))
    
    impApo = Resizer().zScale(impApo, int(impApo.getNSlices() * downsampleZ), 0)
    newW = int(impApo.getWidth() * downsampleXY)
    newH = int(impApo.getHeight() * downsampleXY)    
    impApo.setStack(StackProcessor(impApo.getStack()).resize(newW, newH))
    
    # segment clones and get objects    
    IJ.log("segmenting clones...")
    cloneSegmenter = Segment3DImage(impClones, threshold, Integer.MAX_VALUE)
    cloneSegmenter.setMinSizeObject(minSizeClone)
    cloneSegmenter.segment()    
    cloneObjects = cloneSegmenter.getLabelledObjectsImage3D().getObjects3D()
    IJ.log("segmenting clones... done.")
    IJ.log("found " + str(len(cloneObjects)) + " clones.")
    
    # segment clones and get objects    
    IJ.log("segmenting apoptosis...")
    apoSegmenter = Segment3DImage(impApo, threshold, Integer.MAX_VALUE)
    apoSegmenter.setMinSizeObject(minSizeApo)
    apoSegmenter.segment()    
    apoObjects = apoSegmenter.getLabelledObjectsImage3D().getObjects3D()
    IJ.log("segmenting apoptosis... done.")
    IJ.log("found " + str(len(apoObjects)) + " apoptosis sites.")
    
    cloneSizes = dict()
    apoSizes = dict()
    
    for i in range(len(cloneObjects)):
        cloneSizes[i] = cloneObjects[i].getVolumePixels()
        apoSizes[i] = list()
    
    nApo = len(apoObjects)
    nApoInClones = 0
    for i in range(len(apoObjects)):
        o = apoObjects[i]
        apoCenter = Point3D(o.getCenterX(), o.getCenterY(), o.getCenterZ())
        for j in range(len(cloneObjects)):
           # if cloneObjects[j].inside(apoCenter):
            if cloneObjects[j].includes(o):
                IJ.log("Handling apo site " + str(i+1) + " of " + str(nApo))
                apoSizes[j].append((i, o.getVolumePixels()))
                nApoInClones += 1
                break
    
    IJ.log(str(nApoInClones) + " of " + str(nApo) + "apoptosis sites mapped to clones.")
    
    # create control image
    imageControl = impClones.duplicate()
    StackConverter(imageControl).convertToRGB()
    for c in cloneObjects:
        c.draw(imageControl.getStack(), 255, 0, 0)
    for a in apoObjects:
        a.draw(imageControl.getStack(), 0, 255, 0)
    IJ.save(imageControl, os.path.join(os.path.sep.join(pathClones.split(os.path.sep)[:-1]), "controll.tif"))
    
    apoSizesRes = dict()
    for k, v in apoSizes.items():
        #print v
        apoSizesRes[k] = reduce(lambda x, y: x + y[1], v ,0)
        
    return cloneSizes, apoSizesRes
            
        



def mainApoptosisAnalysis():
    dc = DirectoryChooser("Choose directory to process!")
    inputDir = dc.getDirectory()
    
    outfd = open(os.path.join(inputDir, "results.csv"), "w")
    
    apoFilename = "ch01 and ch03_binary_fill holes.tif"
    cloneFilename = "ch01_binary_fill holes.tif"
    
    cloneSize, apoSize = apoptosisAnalyis(os.path.join(inputDir, cloneFilename), os.path.join(inputDir, apoFilename))
    
    outfd.write("clone_size;apo_size\n")
    
    for i in cloneSize.keys():
        outfd.write(str(cloneSize[i]) + ";" + str(apoSize[i]) + "\n")
    
    outfd.close()
    IJ.log("--All done--")
'''
MAIN
'''
if __name__ == "__main__":
    mainApoptosisAnalysis()