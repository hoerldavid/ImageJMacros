from ij import WindowManager, IJ, ImagePlus, ImageStack
from ij.process import StackConverter, ByteProcessor
from ij.process import ColorProcessor
from ij.plugin.frame import RoiManager
from ij.plugin.filter import Analyzer
from ij.measure import ResultsTable
from ij.plugin.filter import ParticleAnalyzer

from java.lang import Integer
from java.awt.Color import BLACK, WHITE, RED, GREEN

import os

# USER INPUT
path = "C:\Users\David\Desktop\\150211 live U2OS_GFP export\\Kinetik 7\\"
filename = "GFP FKBP-LacI-RFP recruitment kinetic 7"

filename = filename + "c1_cut.tiff"

# SETTINGS
outFileName = "kintetic.csv"

timesDilate1 = 3
timesDilate2 = 5
minParticleSize = 20
minCircularity = 0.6

classifiedImageName = "Classified image"
classifiedImage = WindowManager.getImage(classifiedImageName)

# load image to measure in
impSignal = IJ.openImage(os.path.join(path, filename))
impSignal.show()


# make image binary
StackConverter(classifiedImage).convertToGray8()
for i in range(1, classifiedImage.getNSlices()+1):
    classifiedImage.setSlice(i)
    classifiedImage.getProcessor().autoThreshold()

# get rm, rt and analyzer    
rm = RoiManager.getInstance2()
if not rm:
    rm = RoiManager()    
rt = Analyzer.getResultsTable()
if not rt:
    rt = ResultsTable()
    Analyzer.setResultsTable(rt)    
pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER , 0 , rt, minParticleSize, Integer.MAX_VALUE, minCircularity, 1.0)


# get ROIs of the segmented blobs
roiList = list()

for i in range(1, classifiedImage.getNSlices()+1):
    classifiedImage.setSlice(i)
    pa.analyze(classifiedImage)
    
    roiList.append(rm.getRoisAsArray())
    rm.deselect()
    rm.reset()

# dilate the blobs twice, save as images (1 blob -> 1 slice)
dilatedStack = ImageStack(classifiedImage.getWidth(), classifiedImage.getHeight())
dilated2Stack = ImageStack(classifiedImage.getWidth(), classifiedImage.getHeight())
   
for sliceRois in roiList:
    for r in sliceRois:
        r.setFillColor(BLACK)
        tBp = ByteProcessor(classifiedImage.getWidth(), classifiedImage.getHeight())
        tBp.setColor(WHITE)
        tBp.fill()
        tBp.drawRoi(r)
        
        for i in range(timesDilate1):
            tBp.dilate()
        
        dilatedStack.addSlice(tBp.duplicate())
        
        for i in range(timesDilate2):
            tBp.dilate()
            
        dilated2Stack.addSlice(tBp.duplicate())

# create dilated blob images, make them binary        
impDilated1 = ImagePlus("", dilatedStack)
impDilated2 = ImagePlus("", dilated2Stack)
StackConverter(impDilated1).convertToGray8()
StackConverter(impDilated2).convertToGray8()
for i in range(1, impDilated1.getNSlices()+1):
    impDilated1.setSlice(i)
    impDilated2.setSlice(i)
    impDilated1.getProcessor().autoThreshold()
    impDilated2.getProcessor().autoThreshold()


# get ROIs for the dilated blobs
dilated1Rois = list()
dilated2Rois = list()
# set minCircularity to 0 -> do not throw away any blobs because of that
pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER , 0 , rt, minParticleSize, Integer.MAX_VALUE, 0, 1.0)
for i in range(1, impDilated1.getNSlices() + 1):
    impDilated1.setSlice(i)
    impDilated2.setSlice(i)
    
    pa.analyze(impDilated1)    
    dilated1Rois.append(rm.getRoisAsArray()[0])
    rm.deselect()
    rm.reset()
    
    pa.analyze(impDilated2)    
    dilated2Rois.append(rm.getRoisAsArray()[0])
    rm.deselect()
    rm.reset()


# DO THE OUTPUT

# open output file + header line
outFd = open(os.path.join(path, outFileName), "w")
outFd.write("blob, slice, ring_mean, ring_area, mean, area \n")

# go through all blobs

controlStack = ImageStack(classifiedImage.getWidth(), classifiedImage.getHeight())
currentRoi = 0    
for i in range(len(roiList)):
    for j in range(len(roiList[i])):
        
        
        outLine = list()
        outLine.append(str(currentRoi))
        outLine.append(str(i))
        
        impSignal.setSlice(i+1)
        
        # get ROIs
        rCenter = roiList[i][j]
        rDilated1 = dilated1Rois[currentRoi]
        rDilated2 = dilated2Rois[currentRoi]        
        # set ROIs to corresponding slice in stack
        rCenter.setPosition(i+1)
        rDilated1.setPosition(i+1)
        rDilated2.setPosition(i+1)
        # ROIs to RoiManager      
        rm.add(impSignal, rCenter, i+1)
        rm.add(impSignal, rDilated1, i+1)
        rm.add(impSignal, rDilated2, i+1)
        
        
        # ring ROI = XOR of dilated ROIs
        rm.setSelectedIndexes([1,2])
        rm.runCommand("XOR") 
        
        # get stats for ring roi, add it to RoiManager
        rRing = impSignal.getRoi()
        rm.add(impSignal, rRing, i+1)

        rm.select(3)
        
        ringStats = impSignal.getStatistics()
        outLine.append(str(ringStats.mean))
        outLine.append(str(ringStats.area))
        rm.deselect()        
        impSignal.killRoi()
        
        # get stats for center roi
        impSignal.setRoi(rCenter)        
        centerStats = impSignal.getStatistics()
        outLine.append(str(centerStats.mean))
        outLine.append(str(centerStats.area))
        impSignal.killRoi()
        
        # reset RoiManger 
        rm.deselect()
        rm.reset()
        
        # print output line
        outFd.write(",".join(outLine) + "\n")
        
        currentRoi += 1
        
        # color ROIs in control image
        tCp = ColorProcessor(classifiedImage.getWidth(), classifiedImage.getHeight())
        rRing.setFillColor(RED)
        rCenter.setFillColor(GREEN)
        tCp.drawRoi(rCenter)
        tCp.drawRoi(rRing)
        controlStack.addSlice(tCp.duplicate())

# show ROI control image                
impControl = ImagePlus("", controlStack)
# impControl.show()

rm.close()
outFd.close()       