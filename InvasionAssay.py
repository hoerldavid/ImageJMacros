'''
Created on 19.02.2015

@author: david
'''


# Evil undocumented APIs !!!
from Utilities import Counter3D
from mcib3d.geom import Object3D, Vector3D
from mcib3d.geom import Object3DPoint, Object3DSurface
from javax.vecmath import Point3f
from java.util import ArrayList



from ij.io import DirectoryChooser
from ij import IJ, ImagePlus
from ij.process import StackConverter

import os
import re
import sys



# User input
channelWithMSC = "1"
channelWithSphero = "2"

spheroThreshold = 15
spheroMin = 1000
spheroMax = 45925560

mscThreshold = 30
mscMin = 200
mscMax = 45925560

# handle Directories starting with any of this
dirPrefixes = ["F", "G"]

def startsWithAny(s, prefixes):
    for p in prefixes:
        if s.startswith(p):
            return True
    return False


def assayMV(path):
    
    files = os.walk(path).next()[2]
    
    fileMSC = ""
    fileSphero = ""
    
    reMSC = re.compile("TP0_Ch" + channelWithMSC + ".*?tif")
    reSphero = re.compile("TP0_Ch" + channelWithSphero + ".*?tif")
    
#     print reMSC.match("TP0_Ch1_Ill0_Ang1,0,2,3,4.tif");
    
    for f in files:
        #print(f)
        if reMSC.match(f):
            fileMSC = os.path.join(path, f)
        elif reSphero.match(f):
            fileSphero = os.path.join(path, f)
    
    
#     fileMSC = os.path.join(path, "TP0_Ch1_Ill0_Ang1,0,2,3,4.tif")
#     fileSphero = os.path.join(path, "TP0_Ch2_Ill0_Ang1,0,2,3,4.tif")


    imageMSC = IJ.openImage(fileMSC)
    imageSphero = IJ.openImage(fileSphero)
    
    StackConverter(imageMSC).convertToGray8()
    StackConverter(imageSphero).convertToGray8()
  #  imageMSC = ImagePlus("mscs", imageMSC.getProcessor().convertToByteProcessor())
   # imageSphero = ImagePlus("sphero", imageSphero.getProcessor().convertToByteProcessor())
    
    
    # imageMSC.show()
    
    counterMSC = Counter3D(imageMSC, mscThreshold, mscMin, mscMax, False, False)
    counterSphero = Counter3D(imageSphero, spheroThreshold, spheroMin, spheroMax, False, False)
    
    print("segmenting mscs...")
    counterMSC.getObjects()
    print("segmenting sphero...")
    counterSphero.getObjects()
    
    # only one object should be in sphero image
    spheroObject1 = counterSphero.getObjectsList()[0]
    
    # image to write control to
    imageControl = imageMSC.duplicate()
    StackConverter(imageControl).convertToRGB()
    
    
    # convert msc objects to points (centers of mass)
    mscObjects = list()
    mscObjects1 = counterMSC.getObjectsList()
    for m in mscObjects1:
        mscObjects.append(Object3DPoint(int(m.mean_gray), m.c_mass[0], m.c_mass[1], m.c_mass[2]))
        
        
        # draw msc contours
        for c in m.surf_voxelsCoord:
            Object3DPoint(1, c[0], c[1], c[2]).draw(imageControl.getStack(), 0, 255, 0)
            
        
        
    print("got msc objects...")
    
    
    
    
    # convert sphero object to surface
    pointlist = ArrayList()
    nVoxels = len(spheroObject1.surf_voxelsCoord)
    curVoxel = 1
    for c in spheroObject1.surf_voxelsCoord:
        sys.stdout.write("handling sphero voxel (" + str(curVoxel) + "/" + str(nVoxels) + ")\r")
        
        #mark surface in red
        point = Point3f(c[0], c[1], c[2])
        Object3DPoint(1, c[0], c[1], c[2]).draw(imageControl.getStack(), 255, 0, 0)
        pointlist.add(point)
        curVoxel = curVoxel + 1
    spheroObject = Object3DSurface(pointlist)
    print("")
    print("got sphero object...")
    
    
    

    # mark sphero in red
    #spheroObject.draw(imageControl.getStack(), 255, 0, 0)
    
    
    # calculate distances
    distances = list()
    for o in mscObjects:
        print("handling a cell...")
        distances.append(o.distCenterBorderUnit(spheroObject))
        # mark mscs in green
        o.draw(imageControl.getStack(), 0, 255, 0)
        
    outfile = os.path.join(path, "distances.csv")
    outfd = open(outfile, "w")
    
    # save cobtrol image
    IJ.save(imageControl, os.path.join(path, "controll.tif"))
    
    outfd.write("distance\r")
    
    for d in distances:
        strValue = str(d)
        strValue.replace(".", ",")
        outfd.write(strValue + "\r")
        
    outfd.close()
        
    return distances



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
    
print("-- Handling multiple input directories:");
for i in sdirs:
    print("- Handing dir: " + i);
    assayMV(i);
    
# quit macro!
sys.exit()