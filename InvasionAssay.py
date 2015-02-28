'''
Created on 19.02.2015

Automated segmentation and invasion depth measurement
(MSCs invading tumor spheroids)

@author: David Hoerl
'''

# Evil undocumented APIs !!!
from Utilities import Counter3D
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


# USER DEFINED PARAMETERS
channelWithMSC = "1"
channelWithSphero = "2"

spheroThreshold = 15
spheroMin = 80000
# spheroMax = Integer.MAX_VALUE

mscThreshold = 90
mscMin = 200
# mscMax = Integer.MAX_VALUE



#downsampleXY = 0.5
downsampleXY = 1
downsampleZ = downsampleXY

# handle Directories starting with any of this
# dirPrefixes = ["F", "G"]

# END USER DEFINED PARAMETERS

def startsWithAny(s, prefixes):
    '''
    check whether s starts with any of the prefixes in prefixes
    '''
    for p in prefixes:
        if s.startswith(p):
            return True
    return False



def assayMV(path, spheroT=spheroThreshold, mscT=mscThreshold, segmentWholeSpheroVolume=False):
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
    mscSegmenter = Segment3DImage(imageMSC, mscT, Integer.MAX_VALUE)
    mscSegmenter.setMinSizeObject(mscMin)
    mscSegmenter.segment()    
    mscObjects = mscSegmenter.getSurfaceObjectsImage3D().getObjects3D()
    IJ.log("segmenting cells... done.")
    IJ.log("found " + str(len(mscObjects)) + " cells.")
    
    # segment the spheroid
    IJ.log("segmenting spheroid...")
    spheroSegmenter = Segment3DImage(imageSphero, spheroT, Integer.MAX_VALUE)
    spheroSegmenter.setMinSizeObject(spheroMin)
    spheroSegmenter.segment()
    
    ### Segment the whole sphero instead of just the surface
    # this allows checking whether a cell lies inside the volume
    # however, the whole volume will be colored in the control image!
    if segmentWholeSpheroVolume:    
        spheroObjects = spheroSegmenter.getLabelledObjectsImage3D().getObjects3D()
    else:
        spheroObjects = spheroSegmenter.getSurfaceObjectsImage3D().getObjects3D()
    IJ.log("segmenting spheroid... done.")
    
    # skip dataset if no sphero was found
    if len(spheroObjects) == 0:
        IJ.log("ERROR: no spheroid could be found")
        return(list(), None)
    
    maxVolume = 0
    biggestObject = 0
    for i in range(len(spheroObjects)):
        if spheroObjects[i].getVolumePixels() > maxVolume:
            biggestObject = i
            maxVolume = spheroObjects[i].getVolumePixels()
            
    spheroObject = spheroObjects[biggestObject]
    
    if len(spheroObjects) != 1:
        IJ.log("WARNING: found " + str(len(mscObjects)) + " spheroid objects. Using the biggest.")
        
    
    # color copy of msc-image to label segmentations in
    imageControl = imageMSC.duplicate()
    StackConverter(imageControl).convertToRGB()
    
    # mark spheroid in red
    spheroObject.draw(imageControl.getStack(), 255, 0, 0)    
    
    #closedSphero = spheroObject.getObject3DSurface()
    #closedSphero.draw(imageControl.getStack(), 0, 0, 255)
    
    # calculate distances
    distances = list()
    nCells = len(mscObjects)
    curCell = 1
    for o in mscObjects:
        IJ.log("handling cell " + str(curCell) + " of " + str(nCells))
        curCell += 1
               
        cellCenter = Point3D(o.getCenterX(), o.getCenterY(), o.getCenterZ())
        
        # skip cells not inside sphero ONLY IF whole sphero was segmented
        if not spheroObject.inside(cellCenter) and segmentWholeSpheroVolume:
            IJ.log("not inside spheroid, skipping.")
            continue
        
        distances.append(o.distCenterBorderUnit(spheroObject))
        # mark mscs in green
        o.draw(imageControl.getStack(), 0, 255, 0)
        
    # save control image
    # IJ.save(imageControl, os.path.join(path, "control.tif"))
    
    # save distances as CSV
    outfile = os.path.join(path, "distances.csv")
    outfd = open(outfile, "w+")    
    
    outfd.write("distance\r")
    
    for d in distances:
        strValue = str(d)
        strValue = strValue.replace('.', ',')
        outfd.write(strValue + "\r")
        
    outfd.close()
    
    return (distances, imageControl)
    
    
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

dc2 = OpenDialog("Choose parameter file!")
paramFile = open(os.path.join(dc2.getDirectory(), dc2.getFileName()), "r")

paramDict = dict()

for l in paramFile:
    ls = l.split(",")
    #print(ls[6].startswith("CELLSOUTSIDE"))
    if ls[1]:
        paramDict["_".join(ls[0:4])] = (int(ls[5]), int(ls[4]), ls[6].startswith("CELLSOUTSIDE"))
    elif ls[0]:
        paramDict["_".join(ls[0:1]+ls[2:4])] = (int(ls[5]), int(ls[4]), ls[6].startswith("CELLSOUTSIDE"))
    
# print(paramDict)   

if inputDir.endswith(os.path.sep):
    inputDir = inputDir[:-1]

    
dirs = os.walk(inputDir)
sdirs = list()
# process only the "mv-workspace" directories   
# of directories starting with specified prefixes
for d in dirs:
    #print(d[0])
    if d[0].split(os.path.sep)[-1] in paramDict.keys() and "mv-workspace" in d[1]:
        sdirs.append(os.path.join(d[0], "mv-workspace"))
    
    
resultFd = open(os.path.join(inputDir, "results.csv"), "w+")
delimiter = ";"

IJ.log("-- Handling multiple input directories:");
for i in sdirs:
    experimentName = i.split(os.path.sep)[-2]
    IJ.log("- Handing dir: " + i);
    IJ.log("msc Threshold: " + str(paramDict[experimentName][0]))
    IJ.log("sphero Threshold: " + str(paramDict[experimentName][1]))
    (tDists, resImage) = assayMV(i, paramDict[experimentName][0], paramDict[experimentName][1], paramDict[experimentName][2]);
    resultFd.write(experimentName + delimiter)
    resultFd.write(delimiter.join(map(str, tDists)).replace('.', ','))
    resultFd.write("\r")
    
    if resImage:
        IJ.save(resImage, os.path.join(inputDir, experimentName + "_control.tif"))
    
    
resultFd.close()

# TODO: clean exit when calling from commandline
# sys.exit()

