'''
Created on 19.02.2015

Automated segmentation and invasion depth measurement
(MSCs invading tumor spheroids)

@author: David Hoerl
'''

# Evil undocumented APIs !!!
from Utilities import Counter3D
from mcib3d.geom import Object3D, Vector3D
from mcib3d.geom import Object3DPoint, Object3DSurface
from mcib3d.image3d import Segment3DImage

from javax.vecmath import Point3f
from java.util import ArrayList
from java.lang import Integer

from ij.plugin import Resizer
from ij.io import DirectoryChooser
from ij import IJ, ImagePlus
from ij.process import StackConverter, StackProcessor

import os
import re
import sys


# USER DEFINED PARAMETERS
channelWithMSC = "1"
channelWithSphero = "2"

spheroThreshold = 15
spheroMin = 80000
# spheroMax = Integer.MAX_VALUE

mscThreshold = 90
mscMin = 200
# mscMax = Integer.MAX_VALUE

downsampleXY = 0.5
# downsampleXY = 1
downsampleZ = downsampleXY

# handle Directories starting with any of this
dirPrefixes = ["F", "G"]

# END USER DEFINED PARAMETERS

def startsWithAny(s, prefixes):
    '''
    check whether s starts with any of the prefixes in prefixes
    '''
    for p in prefixes:
        if s.startswith(p):
            return True
    return False


def assayMV(path):
    '''
    run the invasion assay - image files should be in directory path
    @return: list of distances (in pixels, consider downsampling)
    '''
    
    files = os.walk(path).next()[2]
    
    fileMSC = ""
    fileSphero = ""
    
    # fused/deconvolved (.tif) files should start with TP0_Ch + channel nr.
    reMSC = re.compile("TP0_Ch" + channelWithMSC + ".*?tif")
    reSphero = re.compile("TP0_Ch" + channelWithSphero + ".*?tif")
        
    for f in files:
        # find the two input files
        if reMSC.match(f):
            fileMSC = os.path.join(path, f)
        elif reSphero.match(f):
            fileSphero = os.path.join(path, f)
    
    # load images
    imageMSC = IJ.openImage(fileMSC)
    imageSphero = IJ.openImage(fileSphero)
    
    # convert to 8bit (TODO: set min/max?)
    StackConverter(imageMSC).convertToGray8()
    StackConverter(imageSphero).convertToGray8()

    # downsample images
    imageMSC = Resizer().zScale(imageMSC, int(imageMSC.getNSlices() * downsampleZ), 0)
    newW = int(imageMSC.getWidth() * downsampleXY)
    newH = int(imageMSC.getHeight() * downsampleXY)    
    imageMSC.setStack(StackProcessor(imageMSC.getStack()).resize(newW, newH))
    
    imageSphero = Resizer().zScale(imageSphero, int(imageSphero.getNSlices() * downsampleZ), 0)
    newW = int(imageSphero.getWidth() * downsampleXY)
    newH = int(imageSphero.getHeight() * downsampleXY)    
    imageSphero.setStack(StackProcessor(imageSphero.getStack()).resize(newW, newH))
    
    # segment cells and get objects    
    IJ.log("segmenting cells...")
    mscSegmenter = Segment3DImage(imageMSC, mscThreshold, Integer.MAX_VALUE)
    mscSegmenter.setMinSizeObject(mscMin)
    mscSegmenter.segment()    
    mscObjects = mscSegmenter.getSurfaceObjectsImage3D().getObjects3D()
    IJ.log("segmenting cells... done.")
    IJ.log("found " + str(len(mscObjects)) + " cells.")
    
    # segment the spheroid
    IJ.log("segmenting spheroid...")
    spheroSegmenter = Segment3DImage(imageSphero, spheroThreshold, Integer.MAX_VALUE)
    spheroSegmenter.setMinSizeObject(spheroMin)
    spheroSegmenter.segment()    
    spheroObjects = spheroSegmenter.getSurfaceObjectsImage3D().getObjects3D()
    IJ.log("segmenting spheroid... done.")
    spheroObject = spheroObjects[0]
    if len(spheroObjects) != 1:
        IJ.log("WARNING: found " + str(len(mscObjects)) + " spheroid objects. Will only use first. Cosider re-evaluating thresholds.")
        
    
    # color copy of msc-image to label segmentations in
    imageControl = imageMSC.duplicate()
    StackConverter(imageControl).convertToRGB()
    
    # mark spheroid in red
    spheroObject.draw(imageControl.getStack(), 255, 0, 0)    
    
    # calculate distances
    distances = list()
    nCells = len(mscObjects)
    curCell = 1
    for o in mscObjects:
        IJ.log("handling cell " + str(curCell) + " of " + str(nCells))
        curCell += 1
        distances.append(o.distCenterBorderUnit(spheroObject))
        # mark mscs in green
        o.draw(imageControl.getStack(), 0, 255, 0)
        
    # save control image
    IJ.save(imageControl, os.path.join(path, "control.tif"))
    
    # save distances as CSV
    outfile = os.path.join(path, "distances.csv")
    outfd = open(outfile, "w+")    
    
    outfd.write("distance\r")
    
    for d in distances:
        strValue = str(d)
        strValue = strValue.replace('.', ',')
        outfd.write(strValue + "\r")
        
    outfd.close()
    
    return distances
    
    
#     
#     counterMSC = Counter3D(imageMSC, mscThreshold, mscMin, mscMax, False, False)
#     counterSphero = Counter3D(imageSphero, spheroThreshold, spheroMin, spheroMax, False, False)
#     
#     IJ.log("segmenting mscs...")
#     counterMSC.getObjects()
#     IJ.log("segmenting sphero...")
#     counterSphero.getObjects()
#     
#     # only one object should be in sphero image
#     spheroObject1 = counterSphero.getObjectsList()[0]
#     
#     # image to write control to
#     imageControl = imageMSC.duplicate()
#     StackConverter(imageControl).convertToRGB()
#     
#     
#     # convert msc objects to points (centers of mass)
#     mscObjects = list()
#     mscObjects1 = counterMSC.getObjectsList()
#     for m in mscObjects1:
#         mscObjects.append(Object3DPoint(int(m.mean_gray), m.c_mass[0], m.c_mass[1], m.c_mass[2]))
#         
#         
#         # draw msc contours
#         for c in m.surf_voxelsCoord:
#             Object3DPoint(1, c[0], c[1], c[2]).draw(imageControl.getStack(), 0, 255, 0)
#             
#         
#         
#     IJ.log("got msc objects...")
#     
#     
#     
#     
#     # convert sphero object to surface
#     pointlist = list()
#     nVoxels = len(spheroObject1.surf_voxelsCoord)
#     curVoxel = 1
#     for c in spheroObject1.surf_voxelsCoord:
# #         sys.stdout.write("handling sphero voxel (" + str(curVoxel) + "/" + str(nVoxels) + ")\r")
#         
#         if curVoxel % 10000 == 0:
#             IJ.log("handling sphero vxcel " + str(curVoxel) + " of " + str(nVoxels))
#         
#         #mark surface in red
#         point = Point3f(c[0], c[1], c[2])
#         Object3DPoint(1, c[0], c[1], c[2]).draw(imageControl.getStack(), 255, 0, 0)
# 
#        	pointlist.append(point)
#         curVoxel = curVoxel + 1
#     spheroObject = Object3DSurface(pointlist)
# #     print("")
#     IJ.log("got sphero object...")
#     
#     
#     
# 
#     # mark sphero in red
#     #spheroObject.draw(imageControl.getStack(), 255, 0, 0)
#     
#     
#     # calculate distances
#     distances = list()
#     curCell = 0
#     totalCells = len(mscObjects)
#     for o in mscObjects:
#         curCell = curCell + 1
#         IJ.log("handling cell " + str(curCell) + " of " + str(totalCells))
#         distances.append(o.distCenterBorderUnit(spheroObject))
#         # mark mscs in green
#         o.draw(imageControl.getStack(), 0, 255, 0)
#         
#     outfile = os.path.join(path, "distances.csv")
#     outfd = open(outfile, "w")
#     
#     # save cobtrol image
#     IJ.save(imageControl, os.path.join(path, "controll.tif"))
#     
#     outfd.write("distance\r")
#     
#     for d in distances:
#         strValue = str(d)
#         strValue.replace(".", ",")
#         outfd.write(strValue + "\r")
#         print(d)
#         
#     outfd.close()
#         
#     return distances


# MAIN SCRIPT

# let user pick a directory, process all subdirs
dc = DirectoryChooser("Choose directory to process!")
inputDir = dc.getDirectory()

if inputDir.endswith(os.path.sep):
    inputDir = inputDir[:-1]
dirs = os.walk(inputDir)
sdirs = list()
# process only the "mv-workspace" directories   
# of directories starting with specified prefixes
for d in dirs:
    #print(d[0])
    if startsWithAny(d[0].split(os.path.sep)[-1], dirPrefixes) and "mv-workspace" in d[1]:
        sdirs.append(os.path.join(d[0], "mv-workspace"))
    
    
resultFd = open(os.path.join(inputDir, "results.csv"), "w+")
delimiter = ";"

IJ.log("-- Handling multiple input directories:");
for i in sdirs:
    IJ.log("- Handing dir: " + i);
    tDists = assayMV(i);
    resultFd.write(i + delimiter)
    resultFd.write(delimiter.join(map(str, tDists)).replace('.', ','))
    resultFd.write("\r")
    
resultFd.close()

# TODO: clean exit when calling from commandline
# sys.exit()

