'''
Created on 02.03.2015

@author: David
'''

from ij.io import DirectoryChooser
from ij import IJ, ImagePlus

import glob
import os
import sys
import shutil

dc = DirectoryChooser("Pick directory!")
inPath = dc.getDirectory()

dirs = os.walk(inPath)

# DANGER : this only worked in my special case
#           to remove whitespaces from directories
#
# for (p, d, f) in dirs:
#     if p != p.replace(" ", ""):
#         shutil.move(p, p.replace(" ", ""))
#     
# dirs = os.walk(inPath)

for (p, d, f) in dirs:
     
    path = p
    
    if not path.endswith(os.sep):
            path += os.sep;
    
    imageFilesBlue = glob.glob(path + "*ch00.tif");
    imageFilesGreen = glob.glob(path + "*ch01.tif");
    imageFilesRed = glob.glob(path + "*ch02.tif");
    
    print(imageFilesBlue)
    
    # skip folders w/o images
    if not imageFilesBlue:
        continue
    
    
    blueStack = None
    greenStack = None
    redStack = None
    
    for i in imageFilesBlue:
        img = IJ.openImage(i)
        if not blueStack:
            blueStack = img.createEmptyStack()
        blueStack.addSlice(img.getProcessor())
    blueStackImage = ImagePlus("blue", blueStack)
        
    for i in imageFilesGreen:
        img = IJ.openImage(i)
        if not greenStack:
            greenStack = img.createEmptyStack()
        greenStack.addSlice(img.getProcessor())
    greenStackImage = ImagePlus("green", greenStack)
    
    
    for i in imageFilesRed:
        img = IJ.openImage(i)
        if not redStack:
            redStack = img.createEmptyStack()
        redStack.addSlice(img.getProcessor())
    redStackImage = ImagePlus("red", redStack)
    
    # get rid of separator    
    path = path[:-1]
    
    redOutFile = os.path.join(path, "r_" + path.split(os.sep)[-1] + ".tif")
    greenOutFile = os.path.join(path, "g_" + path.split(os.sep)[-1] + ".tif")
    blueOutFile = os.path.join(path, "b_" + path.split(os.sep)[-1] + ".tif")
    
    IJ.saveAsTiff(redStackImage, redOutFile)
    IJ.saveAsTiff(greenStackImage, greenOutFile)
    IJ.saveAsTiff(blueStackImage, blueOutFile)

sys.exit()
