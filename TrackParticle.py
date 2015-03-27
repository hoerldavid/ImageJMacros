from ij import WindowManager, IJ, ImagePlus, ImageStack
from ij.process import StackConverter, StackProcessor, ByteProcessor
from ij.plugin.frame import RoiManager
from ij.plugin.filter import Analyzer
from ij.measure import ResultsTable
from ij.plugin.filter import ParticleAnalyzer

from java.lang import Integer
from java.awt.Color import BLACK, WHITE


classifiedImageName = "Classified image"
classifiedImage = WindowManager.getImage(classifiedImageName)

timesDilate1 = 3
timesDilate2 = 5

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
    
pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER , 0 , rt, 0, Integer.MAX_VALUE, 0, 1.0)

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

impDilated1.show()
impDilated2.show()
        