

#    Analysis of chromobody uptake
#    David Hoerl
#    started 2015/06/21


from ij import IJ, ImagePlus
from ij.plugin import ImageCalculator
from ij.process import ImageProcessor, StackConverter
from ij.plugin.frame import RoiManager
from ij.plugin.filter import Analyzer
from ij.measure import ResultsTable, Measurements
from ij.plugin.filter import ParticleAnalyzer, Binary

from java.lang import Float, Integer, Short

from jarray import zeros


# radius of DoG
sigma1 = 1.0
sigma2 = 5.0

# size of lamin particles
minLaminSize = 500

#min size of dilated cells
minCellSize = 2500

# number of dilation iterations
timesDilate1 = 3
timesDilate2 = 5
timesDilateChromo = 10

impRaw = IJ.getImage()

# set ROI manger and ResultsTable
rm = RoiManager.getInstance2()
if not rm:
    rm = RoiManager()
    
rt = Analyzer.getResultsTable()
if not rt:
    rt = ResultsTable()
    Analyzer.setResultsTable(rt)

# GFP image = first image in stack
impRaw.setSlice(1)
impGFP = ImagePlus("GFP", impRaw.getProcessor().duplicate())

# chromobody image = second image in stack
impRaw.setSlice(2)
impChromo = ImagePlus("chromobody", impRaw.getProcessor().duplicate())


# segment vesicles (autoThreshold)
vesicleMax = impChromo.getStatistics().max
# FIXME: do good thresholding here!!!
impChromo.getProcessor().setThreshold(impChromo.getProcessor().getAutoThreshold(), Integer.MAX_VALUE, ImageProcessor.RED_LUT)
pa = ParticleAnalyzer(ParticleAnalyzer.SHOW_MASKS , 0 , rt, 0, Integer.MAX_VALUE, 0, 1.0)
pa.analyze(impChromo)
impChromoMask = pa.getOutputImage()
impChromoMask.show()

for i in range(timesDilateChromo):
    impChromoMask.getProcessor().dilate()

# calculate difference-of-gaussian of lamin-GFP
impDoG1 = ImagePlus("DoG1", impGFP.getProcessor().duplicate())
impDoG1.getProcessor().blurGaussian(sigma1)
impDoG2 = ImagePlus("DoG2", impGFP.getProcessor().duplicate())
impDoG2.getProcessor().blurGaussian(sigma2)

impDoG = ImageCalculator().run("Subtract create 32bit", impDoG1, impDoG2)
impDoG.show()

DoGMean = impDoG.getStatistics().mean
DogSD = impDoG.getStatistics().stdDev

impDoG.getProcessor().setThreshold(DoGMean + 0.1 * DogSD, Integer.MAX_VALUE, ImageProcessor.RED_LUT)

# segment lamin
pa = ParticleAnalyzer(ParticleAnalyzer.SHOW_MASKS , 0 , rt, minLaminSize, Integer.MAX_VALUE, 0, 1.0)
pa.analyze(impDoG)
impLaminMask = pa.getOutputImage()

impCells1 = ImagePlus("cells1_for_binary_fill_holes", impLaminMask.getProcessor().duplicate())
for i in range(timesDilate1):
    impCells1.getProcessor().dilate()
impCells1.show()
IJ.selectWindow("cells1_for_binary_fill_holes")
IJ.run("Fill Holes")
impCells1.hide()

impCells2 = ImagePlus("cells", impCells1.getProcessor().duplicate())
for i in range(timesDilate2):
    impCells2.getProcessor().dilate()
       
impCytoplasmaticRing = ImageCalculator().run("XOR create", impCells1, impCells2)
impCytoplasmaticRing.show()

# get Mask of Just Cells in middle
pa = ParticleAnalyzer(ParticleAnalyzer.SHOW_MASKS + ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES , 0 , rt, minCellSize, Integer.MAX_VALUE, 0, 1.0)
pa.analyze(impCells2)
impCellsMid = pa.getOutputImage()
impCellsMid.show()

impRingAndVesicle = ImageCalculator().run("AND create", impCytoplasmaticRing, impChromoMask)
impLaminaAndVesicle = ImageCalculator().run("AND create", impLaminMask, impChromoMask)

impRingNoVesicle = ImageCalculator().run("XOR create", impCytoplasmaticRing, impRingAndVesicle)
impLaminaNoVesicle = ImageCalculator().run("XOR create", impLaminMask, impLaminaAndVesicle)

# scale up to 16bit
lutTo16Bit = zeros(65536, 'i')
lutTo16Bit[255] = 65535
impRingNoVesicle.setProcessor(impRingNoVesicle.getProcessor().convertToShortProcessor())
impRingNoVesicle.getProcessor().applyTable(lutTo16Bit)
impLaminaNoVesicle.setProcessor(impLaminaNoVesicle.getProcessor().convertToShortProcessor())
impLaminaNoVesicle.getProcessor().applyTable(lutTo16Bit)

impRingNoVesicle.show()
impLaminaNoVesicle.show()

impRingSignal = ImageCalculator().run("AND create", impChromo, impRingNoVesicle)
impLaminaSignal = ImageCalculator().run("AND create", impChromo, impLaminaNoVesicle)
impLaminaGFPSignal = ImageCalculator().run("AND create", impGFP, impLaminaNoVesicle)

impRingSignal.show()
impLaminaSignal.show()

rm.reset()
pa = ParticleAnalyzer(ParticleAnalyzer.ADD_TO_MANAGER , 0 , rt, minCellSize, Integer.MAX_VALUE, 0, 1.0)
pa.analyze(impCellsMid)
rois = rm.getRoisAsArray()


Analyzer.setMeasurements(Measurements.INTEGRATED_DENSITY)

analyzerRingMask = Analyzer(impRingNoVesicle)
analyzerRing = Analyzer(impRingSignal)
analyzerLaminaMask = Analyzer(impLaminaNoVesicle)
analyzerLamina = Analyzer(impLaminaSignal)

rt.reset()

rm.runCommand(impRingSignal, "Measure")
rm.runCommand(impRingNoVesicle, "Measure")
rm.runCommand(impLaminaSignal, "Measure")
rm.runCommand(impLaminaNoVesicle, "Measure")
#rm.runCommand(impLaminaGFPSignal, "Measure")
rt.show("Results")
print(rt.size())
for i in range(len(rois)):
    areaRing = rt.getValue("IntDen", len(rois) + i)/65535
    areaLamina = rt.getValue("IntDen", 3*len(rois) + i)/65535
    meanRing = rt.getValue("IntDen", i)/areaRing
    meanLamina = rt.getValue("IntDen", 2*len(rois) +i)/areaLamina
    #meanLaminaGFP = rt.getValue("IntDen", 2*len(rois) +i)/areaLamina
    
    print ((meanRing, meanLamina, meanLamina/meanRing))