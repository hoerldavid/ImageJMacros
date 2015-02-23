'''
Created on 19.02.2015

@author: david
'''


# Evil undocumented APIs !!!
from Utilities import Counter3D
from mcib3d.geom import Object3D, Vector3D

from ij.io import DirectoryChooser
from ij import IJ, ImagePlus

import os
import re


# User input
channelWithMSC = "1"
channelWithSphero = "2"

spheroThreshold = 160
spheroMin = 80000
spheroMax = 45925560

mscThreshold = 90
mscMin = 400
mscMax = 45925560


def assayMV(path):
    
    files = os.walk(path).next()[2]
    
    fileMSC = ""
    fileSphero = ""
    
    reMSC = re.compile("[.]*Ch" + channelWithMSC + "[.]*\.tif")
    reSphero = re.compile("[.]*Ch" + channelWithSphero + "[.]*\.tif")
    
    for f in files:
        if reMSC.match(f):
            fileMSC = os.path.join(path, f)
        elif reSphero.match(f):
            fileSphero = os.path.join(path, f)
    
    imageMSC = IJ.openImage(fileMSC)
    imageSphero = IJ.openImage(fileSphero)
    
    counterMSC = Counter3D(imageMSC, mscThreshold, mscMin, mscMax, False, False)
    counterSphero = Counter3D(imageSphero, spheroThreshold, spheroMin, spheroMax, False, False)
    
    counterMSC.getObjects()
    counterSphero.getObjects()
    
    # TODO: continue here
    



# let user pick a directory, process all subdirs
dc = DirectoryChooser("Choose directory to process!")
inputDir = dc.getDirectory()
dirs = os.walk(inputDir)
sdirs = list()
# process only the "mv-workspace" directories   
for d in dirs:
    if d[0].endswith("mv-workspace"):
        sdirs.append(d[0])
    
print("-- Handling multiple input directories:");
for i in sdirs:
    print("- Handing dir: " + i);
    assayMV(i);