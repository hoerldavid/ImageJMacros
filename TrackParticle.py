from ij import WindowManager, IJ, ImagePlus, ImageStack
from ij.process import StackConverter, StackProcessor, ByteProcessor
from ij.plugin.frame import RoiManager
from ij.plugin.filter import Analyzer
from ij.measure import ResultsTable
from ij.plugin.filter import ParticleAnalyzer

from java.lang import Integer
from java.awt.Color import BLACK, WHITE

import os


path = "/Users/david/Desktop/Kinetik 7"
fileName = "GFP FKBP-LacI-RFP recruitment kinetic 7c1_cut.tiff"


classifiedImageName = "Classified image"
classifiedImage = WindowManager.getImage(classifiedImageName)

timesDilate1 = 3
timesDilate2 = 5

minParticleSize = 10

# load image to measure in
impSignal = IJ.openImage(os.path.join(path, fileName))
impSignal.show()


# make image binary
StackConverter(classifiedImage).convertToGray8()
for i in range(1, classifiedImage.getNSlices()+1):
    classifiedImage.setSlice(i)
    classifiedImage.getProcessor().autoThreshold()
    
rm = RoiManager.getInstance2()
if not rm:
    rm = RoiManager()
    
rt = Analyzer.getResultsTable()
if not rt:
    rt = ResultsTable()
    Analyzer.setResultsTable(rt)
    
pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER , 0 , rt, minParticleSize, Integer.MAX_VALUE, 0, 1.0)

roiList = list()

dilatedStack = ImageStack(classifiedImage.getWidth(), classifiedImage.getHeight())
dilated2Stack = ImageStack(classifiedImage.getWidth(), classifiedImage.getHeight())

for i in range(1, classifiedImage.getNSlices()+1):
    classifiedImage.setSlice(i)
    pa.analyze(classifiedImage)
    
    roiList.append(rm.getRoisAsArray())
    rm.deselect()
    rm.reset()
    
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
        
impDilated1 = ImagePlus("", dilatedStack)
impDilated2 = ImagePlus("", dilated2Stack)
StackConverter(impDilated1).convertToGray8()
StackConverter(impDilated2).convertToGray8()
for i in range(1, impDilated1.getNSlices()+1):
    impDilated1.setSlice(i)
    impDilated2.setSlice(i)
    impDilated1.getProcessor().autoThreshold()
    impDilated2.getProcessor().autoThreshold()



dilated1Rois = list()
dilated2Rois = list()

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

currentRoi = 0    
for i in range(len(roiList)):
    for j in range(len(roiList[i])):
        
        impSignal.setSlice(i+1)
        rCenter = roiList[i][j]
        rDilated1 = dilated1Rois[currentRoi]
        rDilated2 = dilated2Rois[currentRoi]
        
        rm.addRoi(rCenter)
        rm.addRoi(rDilated1)
        rm.addRoi(rDilated2)
        rm.setSelectedIndexes([1,2])
        rm.runCommand("XOR")
        
        rRing = impSignal.getRoi()
        print "ring", impSignal.getStatistics().toString()
        impSignal.killRoi()
        
        impSignal.setRoi(rDilated1)
        
        print "dilated1", impSignal.getStatistics().toString()
        
        impSignal.killRoi()
        
        impSignal.setRoi(rDilated2)
        
        print "dilated2", impSignal.getStatistics().toString()
        
        impSignal.killRoi()
        
        #rm.selectAndMakeVisible(impSignal, currentRoi * 3)
        impSignal.setRoi(rCenter)
        
        print "center", impSignal.getStatistics().toString()
        
        impSignal.killRoi()
        
        rm.deselect()
        rm.reset()
    
        currentRoi += 1


impDilated1.show()
impDilated2.show()
        